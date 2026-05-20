# Admin Dashboard Plan — wetMud Studios

_Drafted 2026-05-20. Source-of-truth for the admin/CMS build._

## Recommendation up front

**Extend the existing `leadgen-crm/` Express server** as the admin backend. Don't add FastAPI. Don't add Supabase yet. Already in repo:

- Express + `better-sqlite3` running on Node
- Bearer-token auth middleware (`leadgen-crm/server.js` lines 9–17)
- Anthropic SDK wired up
- Static file serving + a working admin-style UI under `leadgen-crm/public/`

This becomes one server hosting: (a) the lead CRM, (b) the new content admin, and eventually (c) the client portal. One deploy, one auth, one DB file per concern.

For Phase 4 (client portal), **port the SteltmanDesign architecture** when there's a real client. It's heavyweight (Supabase + RLS + magic links) — appropriate for the dad-handoff use case there, overkill until we have a paying client here.

## Why not the Agentic-biz Python backend

- FastAPI + Supabase + Redis + Stripe is built for a SaaS with billing
- creativeagency is a brochure site that needs CRUD on ~30 rows of content
- Wrong tool. Skip.

## Architecture

```
creativeagency/
├── index.html              ← becomes a renderer (fetches data/site.json)
├── blog.html               ← becomes a renderer (fetches data/site.json)
├── images/                 ← still git-tracked for hero/static assets
├── uploads/                ← NEW: admin-uploaded images (gitignored)
├── data/
│   └── site.json           ← NEW: published snapshot, served by GH Pages
├── content.db              ← NEW: SQLite for editable content (separate from leads.db)
└── leadgen-crm/
    ├── server.js           ← add /api/content/* + /api/uploads routes
    ├── public/
    │   ├── index.html      ← existing CRM dashboard
    │   ├── admin.html      ← NEW: content editor (Site / Projects / Blog / Media)
    │   └── admin.js
    └── migrations/
        └── 001_content.sql ← NEW: schema for projects, posts, site_settings, media
```

**Publish flow (the killer feature):**

1. Admin edits content live against the Express server
2. Hits "Publish" → server writes `creativeagency/data/site.json`
3. Server git-commits + pushes that file → GitHub Pages serves the static snapshot
4. Live site loads `data/site.json` (zero backend dependency for visitors)
5. Admin server only needs to be running *while editing*

Best of both worlds — static-host speed for visitors, dynamic editing for the operator.

## Schema (`migrations/001_content.sql`)

```sql
CREATE TABLE site_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT DEFAULT (datetime('now'))
);
-- rows: hero_headline, hero_subcopy, tagline, contact_email, formspree_id, about_text

CREATE TABLE services (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sort_order INTEGER NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  visible INTEGER DEFAULT 1
);

CREATE TABLE projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sort_order INTEGER NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  blurb TEXT NOT NULL,
  tags TEXT,                -- comma-separated
  url TEXT,
  image_path TEXT,          -- /uploads/xyz.png or /images/xyz.png
  card_size TEXT DEFAULT 'half',  -- wide | narrow | half
  visible INTEGER DEFAULT 1,
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  date TEXT NOT NULL,       -- ISO yyyy-mm-dd
  tag TEXT,
  excerpt TEXT,
  body_md TEXT NOT NULL,
  body_html TEXT,           -- rendered cache
  cover_image TEXT,
  published INTEGER DEFAULT 0,
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  path TEXT NOT NULL,
  size_bytes INTEGER,
  uploaded_at TEXT DEFAULT (datetime('now'))
);
```

## API surface (new routes in `server.js`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/api/content/site.json` | none | Public bundle for renderer |
| `GET` | `/api/content/projects` | bearer | List |
| `POST` | `/api/content/projects` | bearer | Create |
| `PATCH` | `/api/content/projects/:id` | bearer | Update |
| `DELETE` | `/api/content/projects/:id` | bearer | Delete |
| `POST` | `/api/content/projects/reorder` | bearer | Bulk sort_order |
| `GET POST PATCH DELETE` | `/api/content/posts/*` | bearer | Blog CRUD |
| `GET PATCH` | `/api/content/settings` | bearer | Hero, about, contact |
| `POST` | `/api/media/upload` | bearer | multipart → uploads/ |
| `GET` | `/api/media` | bearer | List uploaded images |
| `POST` | `/api/content/publish` | bearer | Writes data/site.json + git push |
| `POST` | `/api/content/draft-post` | bearer | Claude-assisted blog draft |

Reuse the existing `ACCESS_TOKEN` bearer middleware. Only `GET /api/content/site.json` is public.

## Admin UI (`leadgen-crm/public/admin.html`)

Vanilla HTML/CSS/JS. Match wetMud's design tokens. Sidebar + tabbed content:

```
┌─ wetMud Admin ──────────────────────────────┐
│ Site Settings   │  [editor pane]            │
│ Services        │                            │
│ Projects     ●  │   Title: ___________      │
│ Blog Posts      │   Blurb: [textarea]       │
│ Media Library   │   Image: [drop zone]      │
│ Leads (CRM)     │   Tags:  ___________      │
│ Publish ▸       │   [Save] [Delete]         │
└─────────────────┴───────────────────────────┘
```

**Steal from `SteltmanDesign/js/admin.js`** (2628 lines — lots to crib):

- Drag-drop upload pattern
- Toast notifications
- Modal edit pattern
- Magic-link auth flow (deferred to Phase 4)

**Blog editor:** `<textarea>` + side-by-side preview using `marked` (single CDN script). "Draft with AI" button → POST `/api/content/draft-post` `{ topic, voice: "wetmud" }` → reuses Anthropic key + the `user_writing_style.md` memory as system prompt.

## Renderer changes

`index.html` (1197 lines) currently has services and project cards as static HTML.

1. Replace lines 892–935 (services) with `<div id="services-grid"></div>` + render fn
2. Replace lines 940–1037 (work grid) with `<div id="work-grid"></div>` + render fn
3. Replace lines 1091–1118 (about) with `<div id="about-content"></div>`
4. Add `<script>` at body end that fetches `data/site.json` (static-published) or `/api/content/site.json` (live admin), then renders

`blog.html`: swap the hardcoded `POSTS` array (line 490) for the same fetch pattern.

**Discipline:**

- Use `DocumentFragment` + `textContent` (not `innerHTML`) when rendering user-editable copy — matches `SteltmanDesign/js/admin.js` and `leadgen-crm/public/` patterns
- Cache fetched JSON in `localStorage` with 5-min TTL — if admin server is down and `site.json` hasn't been published, site renders from last good snapshot

## Build phases

### Phase 1 — Content admin (1–2 sessions)

1. Add `migrations/001_content.sql`, run once to create `content.db`
2. One-shot `scripts/seed-from-html.js` to extract current hardcoded content
3. API routes in `server.js`
4. `admin.html` tabs: Site / Services / Projects / Blog / Media
5. Convert `index.html` and `blog.html` to render from `site.json`
6. `npm run publish` → writes `data/site.json`, commits, pushes

### Phase 2 — Media handling (1 session)

1. `multer` for uploads (only new dep)
2. `sharp` for resize on upload (optional, cheap page-speed win)
3. Drag-drop UI in admin

### Phase 3 — Authoring polish (1 session)

1. Markdown editor with live preview
2. Claude-assisted draft endpoint (Haiku, already wired)
3. Auto-save drafts every 30s
4. Image library picker inside blog editor

### Phase 4 — Client portal (later, when first client signs)

Port `SteltmanDesign/`:

- `clients` table + token-gated portal pages (steal `sql/01_schema.sql` and `sql/04_functions.sql` patterns, translate to SQLite)
- `/portal/[token]` route serving videos / file deliveries / status updates
- Client invite flow from admin → magic link or token URL
- **Decision needed at Phase 4:** stay on SQLite or graduate to Supabase. SteltmanDesign chose Supabase for dad-handoff + RLS. We may not need that.

## Deployment

- **Public site:** stays on GitHub Pages + Cloudflare. Zero change.
- **Admin server:** Railway. One service, ~$5/mo. Env: `ACCESS_TOKEN`, `ANTHROPIC_API_KEY`, `GH_TOKEN` (for the publish push). Mount a Railway volume for `content.db`, `leads.db`, `uploads/`.
- **Backups:** nightly cron `cp content.db content-$(date).db` into volume + GitHub API snapshot upload.

## What to skip

- No framework (CLAUDE.md mandate — vanilla HTML/CSS/JS)
- No FastAPI / Python backend (wrong tool)
- No WYSIWYG editor (markdown + preview is enough)
- No magic-link auth in Phase 1 (bearer token in localStorage is fine for one user)

## Recommended kickoff

**Spike the renderer change first** — prove the static-publish JSON flow works end-to-end on a single section (Projects) before committing to the full plan. ~30 min, validates the architecture, surfaces wrong assumptions early.
