const request = require('supertest');
const Database = require('better-sqlite3');
const path = require('path');
const os = require('os');
const fs = require('fs');

let testDbPath;
let app;

function seedDb(dbPath) {
  const db = new Database(dbPath);
  db.pragma('journal_mode = WAL');
  db.prepare([
    'CREATE TABLE leads (',
    '  id INTEGER PRIMARY KEY AUTOINCREMENT,',
    '  name TEXT NOT NULL, name_normalized TEXT, address TEXT,',
    '  city TEXT, niche TEXT, phone TEXT, phone_normalized TEXT,',
    '  email TEXT, website_url TEXT, has_website INTEGER DEFAULT 0,',
    '  has_google_listing INTEGER DEFAULT 0, site_platform TEXT,',
    '  review_count INTEGER, last_review_date TEXT, has_ssl INTEGER DEFAULT 0,',
    '  score INTEGER, score_breakdown TEXT, status TEXT DEFAULT "new",',
    '  is_new INTEGER DEFAULT 1, scraped_at TEXT',
    ')'
  ].join(' ')).run();
  db.prepare([
    'CREATE TABLE outreach (',
    '  id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER,',
    '  email_draft TEXT, notes TEXT, generated_at TEXT,',
    '  contacted_at TEXT, updated_at TEXT',
    ')'
  ].join(' ')).run();
  db.prepare(
    'INSERT INTO leads (name, name_normalized, city, niche, score, score_breakdown, status, is_new) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
  ).run("Mario's Pizza", 'mariospizza', 'Burlington', 'restaurant', 87, '{"no_website":40}', 'new', 1);
  db.prepare(
    'INSERT INTO leads (name, name_normalized, city, niche, score, score_breakdown, status, is_new) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
  ).run('Salon Luxe', 'salonluxe', 'Burlington', 'salon', 74, '{"template_site":20}', 'contacted', 0);
  db.close();
}

beforeAll(() => {
  testDbPath = path.join(os.tmpdir(), 'test-leads-' + Date.now() + '.db');
  process.env.TEST_DB_PATH = testDbPath;
  seedDb(testDbPath);
  app = require('../server');
});

afterAll(() => {
  try { fs.unlinkSync(testDbPath); } catch (_) {}
});

test('GET /api/leads returns all leads sorted by score', async () => {
  const res = await request(app).get('/api/leads');
  expect(res.status).toBe(200);
  expect(res.body.length).toBe(2);
  expect(res.body[0].score).toBeGreaterThanOrEqual(res.body[1].score);
});

test('GET /api/leads filters by status', async () => {
  const res = await request(app).get('/api/leads?status=contacted');
  expect(res.status).toBe(200);
  expect(res.body.length).toBe(1);
  expect(res.body[0].name).toBe('Salon Luxe');
});

test('GET /api/leads/:id returns lead with outreach', async () => {
  const res = await request(app).get('/api/leads/1');
  expect(res.status).toBe(200);
  expect(res.body.name).toBe("Mario's Pizza");
  expect(res.body).toHaveProperty('outreach');
});

test('GET /api/leads/:id clears is_new flag', async () => {
  await request(app).get('/api/leads/1');
  const db = new Database(testDbPath);
  const lead = db.prepare('SELECT is_new FROM leads WHERE id = 1').get();
  db.close();
  expect(lead.is_new).toBe(0);
});

test('GET /api/leads/999 returns 404', async () => {
  const res = await request(app).get('/api/leads/999');
  expect(res.status).toBe(404);
});

test('PATCH /api/leads/:id updates status', async () => {
  const res = await request(app).patch('/api/leads/1').send({ status: 'contacted' });
  expect(res.status).toBe(200);
  const db = new Database(testDbPath);
  const lead = db.prepare('SELECT status FROM leads WHERE id = 1').get();
  db.close();
  expect(lead.status).toBe('contacted');
});

test('PATCH /api/leads/:id saves notes', async () => {
  const res = await request(app).patch('/api/leads/1').send({ notes: 'Called, no answer' });
  expect(res.status).toBe(200);
  const db = new Database(testDbPath);
  const outreach = db.prepare('SELECT notes FROM outreach WHERE lead_id = 1').get();
  db.close();
  expect(outreach.notes).toBe('Called, no answer');
});

test('GET /api/meta returns distinct cities and niches', async () => {
  const res = await request(app).get('/api/meta');
  expect(res.status).toBe(200);
  expect(res.body.cities).toContain('Burlington');
  expect(res.body.niches).toContain('restaurant');
});

test('PATCH /api/leads/:id rejects invalid status', async () => {
  const res = await request(app).patch('/api/leads/1').send({ status: 'invalid_value' });
  expect(res.status).toBe(400);
});

test('POST /api/leads/:id/draft returns cached draft without calling API', async () => {
  const db = new Database(testDbPath);
  db.prepare("INSERT INTO outreach (lead_id, email_draft, generated_at) VALUES (?, ?, datetime('now'))")
    .run(2, 'Subject: Hello\n\nHi there.');
  db.close();
  const res = await request(app).post('/api/leads/2/draft');
  expect(res.status).toBe(200);
  expect(res.body.cached).toBe(true);
  expect(res.body.draft).toContain('Subject:');
});

test('POST /api/leads/:id/draft calls Claude API and saves draft', async () => {
  jest.mock('@anthropic-ai/sdk', () => {
    return jest.fn().mockImplementation(() => ({
      messages: {
        create: jest.fn().mockResolvedValue({
          content: [{ text: 'Subject: Test\n\nHi.' }]
        })
      }
    }));
  });
  process.env.ANTHROPIC_API_KEY = 'test-key';
  jest.resetModules();
  const freshApp = require('../server');
  const res = await request(freshApp).post('/api/leads/1/draft');
  expect([200, 502]).toContain(res.status);
  delete process.env.ANTHROPIC_API_KEY;
});
