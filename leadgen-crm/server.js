const express = require('express');
const Database = require('better-sqlite3');
const Anthropic = require('@anthropic-ai/sdk');
const path = require('path');

const app = express();
app.use(express.json());

const ACCESS_TOKEN = process.env.ACCESS_TOKEN;
if (ACCESS_TOKEN) {
  app.use((req, res, next) => {
    const auth = req.headers.authorization || '';
    const token = auth.startsWith('Bearer ') ? auth.slice(7) : req.query.token;
    if (token !== ACCESS_TOKEN) return res.status(401).json({ error: 'Unauthorized' });
    next();
  });
}

app.use(express.static(path.join(__dirname, 'public')));

const DB_PATH = process.env.TEST_DB_PATH || path.join(__dirname, '..', 'leads.db');
const VALID_STATUSES = ['new', 'contacted', 'replied', 'won', 'lost'];

function getDb() {
  const db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');
  return db;
}

app.get('/api/leads', (req, res) => {
  const { city, niche, status, min_score, max_score, search } = req.query;
  const db = getDb();
  const where = [];
  const params = [];

  if (city) { where.push('city = ?'); params.push(city); }
  if (niche) { where.push('niche = ?'); params.push(niche); }
  if (status) { where.push('status = ?'); params.push(status); }
  if (min_score) { where.push('score >= ?'); params.push(Number(min_score)); }
  if (max_score) { where.push('score <= ?'); params.push(Number(max_score)); }
  if (search) { where.push('name LIKE ?'); params.push('%' + search + '%'); }

  const clause = where.length ? 'WHERE ' + where.join(' AND ') : '';
  const leads = db.prepare('SELECT * FROM leads ' + clause + ' ORDER BY score DESC').all(...params);
  db.close();
  res.json(leads);
});

app.get('/api/leads/:id', (req, res) => {
  const db = getDb();
  const lead = db.prepare('SELECT * FROM leads WHERE id = ?').get(req.params.id);
  if (!lead) { db.close(); return res.status(404).json({ error: 'Not found' }); }
  const outreach = db.prepare(
    'SELECT * FROM outreach WHERE lead_id = ? ORDER BY rowid DESC LIMIT 1'
  ).get(req.params.id);
  db.prepare('UPDATE leads SET is_new = 0 WHERE id = ?').run(req.params.id);
  db.close();
  res.json(Object.assign({}, lead, { outreach: outreach || null }));
});

app.patch('/api/leads/:id', (req, res) => {
  const { status, notes } = req.body;
  if (status !== undefined && !VALID_STATUSES.includes(status)) {
    return res.status(400).json({ error: 'Invalid status' });
  }
  if (notes !== undefined && notes.length > 5000) {
    return res.status(400).json({ error: 'Notes too long' });
  }
  const db = getDb();
  const lead = db.prepare('SELECT id FROM leads WHERE id = ?').get(req.params.id);
  if (!lead) { db.close(); return res.status(404).json({ error: 'Not found' }); }
  if (status !== undefined) {
    db.prepare('UPDATE leads SET status = ? WHERE id = ?').run(status, req.params.id);
  }
  if (notes !== undefined) {
    const existing = db.prepare('SELECT id FROM outreach WHERE lead_id = ?').get(req.params.id);
    if (existing) {
      db.prepare('UPDATE outreach SET notes = ?, updated_at = datetime("now") WHERE lead_id = ?')
        .run(notes, req.params.id);
    } else {
      db.prepare('INSERT INTO outreach (lead_id, notes) VALUES (?, ?)').run(req.params.id, notes);
    }
  }
  db.close();
  res.json({ ok: true });
});

app.post('/api/leads/:id/draft', async (req, res) => {
  const db = getDb();
  const lead = db.prepare('SELECT * FROM leads WHERE id = ?').get(req.params.id);
  if (!lead) { db.close(); return res.status(404).json({ error: 'Not found' }); }

  const existing = db.prepare(
    'SELECT email_draft FROM outreach WHERE lead_id = ? AND email_draft IS NOT NULL ORDER BY rowid DESC LIMIT 1'
  ).get(req.params.id);
  if (existing && !req.query.regenerate) {
    db.close();
    return res.json({ draft: existing.email_draft, cached: true });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) { db.close(); return res.status(500).json({ error: 'ANTHROPIC_API_KEY not set' }); }

  let breakdown = {};
  try { breakdown = JSON.parse(lead.score_breakdown || '{}'); } catch (_) {}
  const gaps = Object.keys(breakdown).map(k => k.replace(/_/g, ' ')).join(', ') || 'weak digital presence';

  const client = new Anthropic({ apiKey });
  try {
    const message = await Promise.race([
      client.messages.create({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 400,
        messages: [{
          role: 'user',
          content: 'Write a short, warm, non-pushy outreach email from Jason Steltman at wetMud Studios to a local business owner.\n\n' +
            'Business: ' + lead.name + '\n' +
            'Location: ' + lead.city + ', ON\n' +
            'Type: ' + lead.niche + '\n' +
            'Digital gaps found: ' + gaps + '\n\n' +
            'The email should:\n' +
            '- Be 3-4 short paragraphs\n' +
            '- Reference the specific gap(s) found\n' +
            '- Briefly mention what wetMud Studios does (web design and AI tools for small businesses)\n' +
            '- End with a low-pressure CTA (a quick call or reply)\n' +
            '- Sound like a real person, not a marketing email\n' +
            '- Not use buzzwords like "elevate" or "leverage"\n\n' +
            'Write the subject line first, then the email body.'
        }]
      }),
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 10000))
    ]);

    const draft = message.content[0].text;
    const now = new Date().toISOString().replace('T', ' ').slice(0, 19);
    const existingOutreach = db.prepare('SELECT id FROM outreach WHERE lead_id = ?').get(req.params.id);
    if (existingOutreach) {
      db.prepare('UPDATE outreach SET email_draft = ?, generated_at = ?, updated_at = datetime("now") WHERE lead_id = ?')
        .run(draft, now, req.params.id);
    } else {
      db.prepare('INSERT INTO outreach (lead_id, email_draft, generated_at) VALUES (?, ?, ?)')
        .run(req.params.id, draft, now);
    }
    db.close();
    res.json({ draft, cached: false });
  } catch (err) {
    db.close();
    res.status(502).json({ error: err.message === 'timeout' ? 'Claude API timed out' : 'Failed to generate draft' });
  }
});

app.get('/api/meta', (req, res) => {
  const db = getDb();
  const cities = db.prepare('SELECT DISTINCT city FROM leads WHERE city IS NOT NULL ORDER BY city')
    .all().map(r => r.city);
  const niches = db.prepare('SELECT DISTINCT niche FROM leads WHERE niche IS NOT NULL ORDER BY niche')
    .all().map(r => r.niche);
  db.close();
  res.json({ cities, niches });
});

if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => console.log('CRM running at http://localhost:' + PORT));
}

module.exports = app;
