# Lead Gen Pipeline — Design Spec
**Date:** 2026-03-27
**Project:** wetMud Studios
**Status:** Approved (updated post agent review)

---

## Overview

A two-piece lead generation and CRM pipeline for wetMud Studios. Fetches local business data via Google Places API and scrapes individual business websites for signals, scores leads by digital presence gaps, and surfaces them in a CRM for review and personalized outreach. Built for Jason's own use first, designed clean enough to productize later.

---

## Architecture

Two independent pieces sharing a single SQLite database (`leads.db`):

```
leadgen-scraper/    ← Python CLI, runs locally
leadgen-crm/        ← Node.js + Express app, runs locally or Railway
leads.db            ← shared SQLite database
```

The scraper writes leads. The CRM reads and manages them. No coupling beyond the database schema.

---

## Piece 1 — Scraper CLI

**Location:** `leadgen-scraper/`
**Stack:** Python + Google Places API + requests (for per-site checks)
**Runs:** locally, on-demand

### Usage

```bash
python scrape.py --city Burlington --type restaurant
python scrape.py --city Hamilton --type salon --limit 50
```

### Data Sources

1. **Google Places API** (primary) — Text Search to find businesses, Place Details for website, phone, reviews, GMB status. Free tier: 1,000 requests/month — sufficient for v1 test runs.
2. **Per-site HTTP checks** (enrichment) — for each business with a website URL, make a direct request to detect platform and SSL. Every request wrapped in timeout + try/except.

> **Why not scrape Google Maps directly:** Playwright on Maps triggers bot detection within 10–20 requests. No proxy rotation = no reliable Maps scraping. Places API returns structured data with zero bot risk.
>
> **Why not Yellow Pages / Canada411:** Canada411 has negligible useful data. Yellow Pages rate-limits aggressively and listings are mostly stale. Not worth the fragility for v1.

### Per-Lead Detection

For each business returned by Places API:

- Website URL present or absent (from Places data)
- Website platform detection via HTTP request: check for `/wp-content/` (WordPress), `wix.com` in source/domain, `squarespace.com` in source/domain, `weebly.com`, etc. Platform detection is best-effort (~70–80% accuracy) — displayed in CRM with a confidence note.
- Google Business Profile listing exists (Places API confirms this by returning the record)
- SSL certificate present — checked via direct HTTPS request, independent of Places data
- Review count and date of most recent review (from Places data)
- Business niche/category match

### Scoring Engine (0–100, capped)

| Signal | Points |
|--------|--------|
| No website at all | +40 |
| No Google Business listing | +30 |
| Wix / Squarespace / template site | +20 |
| Few reviews (< 10) or old (> 12 months) | +10 |
| Business niche match (trades, restaurant, salon, etc.) | +10–20 |
| No SSL / broken SSL | +10 |

Score stored as integer, capped at 100. Score breakdown stored as JSON (which signals fired, how many points each).

**Lead tiers:**
- 🔥 Hot: 70–100
- Warm: 40–69
- Cold: 0–39

### Deduplication

Before inserting, normalize name + city + phone: lowercase, strip punctuation, strip whitespace. Check for existing match on normalized composite. Skip if found.

### Output

Writes to `leads.db` with `PRAGMA journal_mode=WAL` set on connection open. Logs progress to terminal including final count: "Scrape complete — 12 new leads added, 3 skipped (duplicates)."

---

## Piece 2 — CRM App

**Location:** `leadgen-crm/`
**Stack:** Node.js + Express, vanilla HTML/CSS/JS frontend, better-sqlite3
**Runs:** locally (`node server.js`) or deployed to Railway

### Layout — Split Panel

```
┌─────────────────────────────────────────────────────────┐
│  [City ▾] [Niche ▾] [Score ▾] [Status ▾]  [Search] [✕] │  ← filter bar + clear
├──────────────────────┬──────────────────────────────────┤
│  Lead List (42)      │  Lead Detail                     │
│                      │                                  │
│  Mario's Pizza  🔥87 │  Mario's Pizza          NEW ●    │
│  Salon Luxe      74  │  Burlington · Restaurant         │
│  Burlington Plmb 68  │  📍 123 Brant St                 │
│  The Bread Oven  55  │  🌐 No website                   │
│  ...                 │  📋 No Google listing            │
│                      │  🔒 No SSL                       │
│                      │                                  │
│  ── empty state ──   │  Score: 87 🔥                    │
│  No leads found.     │  No site +40, No GMB +30,        │
│  Run the scraper     │  Niche +10, Old reviews +7       │
│  to get started.     │                                  │
│                      │  Status: [New ▾]  (auto-saves)   │
│                      │  Notes: [___________] (auto-saves on blur)
│                      │                                  │
│                      │  [✉ Draft Outreach Email]        │
└──────────────────────┴──────────────────────────────────┘
```

### Lead List

- Sorted by score descending by default
- Filter by: city, niche, score range, status
- Search by business name
- Clear filters button (✕) always visible when filters are active
- Hot leads (70+) shown with 🔥 indicator and accent color
- Newly scraped leads show a `NEW` pill — cleared on first click/view
- Empty states:
  - No leads in DB: "No leads yet. Run the scraper to get started."
  - Filters return zero: "No leads match these filters." + [Clear filters] button
- Clicking a row loads detail in right panel

### Lead Detail Panel

- All scraped fields displayed
- Platform detection shown with note: "Detected: Wix (best-effort)"
- Score with full breakdown (all signals that fired)
- Status dropdown: New → Contacted → Replied → Won / Lost — auto-saves on change, shows "Saved ✓" micro-confirmation
- Notes textarea — auto-saves on blur, shows "Saved ✓" micro-confirmation
- "Draft Outreach Email" button

### Outreach Email Drafting

Clicking "Draft Outreach Email":
1. Button changes to "Drafting..." and disables
2. POST to `/api/leads/:id/draft` on the Express server
3. Server calls Claude API (claude-haiku-4-5) with lead data — 10s timeout
4. Prompt includes: business name, city, niche, what's missing, score breakdown
5. On success: draft displayed in panel, copy-to-clipboard button, saved to `outreach` table with `generated_at` timestamp
6. On failure: show inline error "Couldn't generate draft — try again." Button re-enables.
7. If draft already exists: show existing draft immediately (no API call). "Regenerate" link available.

**v2 (future):** Send via Gmail API directly from the CRM.

### Design

Matches wetMud Studios brand DNA:
- Background: `#f5f0e8`, text: `#111111`, accent: `#C84B1A`
- Cabinet Grotesk / Outfit typography
- Directional card shadows
- Dark mode optional (future)

---

## Database Schema

### `leads` table

```sql
CREATE TABLE leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  name_normalized TEXT,           -- lowercase, no punctuation, for deduplication
  address TEXT,
  city TEXT,
  niche TEXT,
  phone TEXT,
  phone_normalized TEXT,          -- for deduplication
  email TEXT,
  website_url TEXT,
  has_website INTEGER DEFAULT 0,  -- boolean, indexed
  has_google_listing INTEGER DEFAULT 0,
  site_platform TEXT,             -- wix, squarespace, wordpress, custom, none, unknown
  review_count INTEGER,
  last_review_date TEXT,          -- ISO 8601 (YYYY-MM-DD), enforced by scraper
  has_ssl INTEGER DEFAULT 0,
  score INTEGER,
  score_breakdown TEXT,           -- JSON
  status TEXT DEFAULT 'new',      -- new, contacted, replied, won, lost
  is_new INTEGER DEFAULT 1,       -- cleared to 0 on first CRM view
  scraped_at TEXT DEFAULT (datetime('now'))
);
```

### `outreach` table

```sql
CREATE TABLE outreach (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lead_id INTEGER REFERENCES leads(id),
  email_draft TEXT,
  notes TEXT,
  generated_at TEXT,              -- when Claude draft was created
  contacted_at TEXT,
  updated_at TEXT DEFAULT (datetime('now'))
);
```

> **Note:** `status` lives on `leads`, not `outreach`. `outreach` is for draft + contact history only. Both connections (scraper and CRM) must set `PRAGMA journal_mode=WAL` on open.

---

## Entry Point on creativeagency Site

Add a small linked card to the creativeagency `index.html` — private/subtle placement (footer). Points to the CRM app URL (Railway or localhost during dev).

---

## Out of Scope — v1

- Gmail send (designed for, not built)
- Scheduled scraping (designed for, not built)
- Auth / password protection
- Multi-user / multi-tenant
- Kanban pipeline view
- Mobile layout
- Proxy rotation / CAPTCHA solving

---

## Future Roadmap

- **v1.1** — Gmail send integration
- **v1.2** — Scheduled scraping (cron)
- **v1.3** — Kanban pipeline view
- **v2** — Auth + multi-user (productize for other freelancers/agencies)
- **v2.1** — AI-generated tool proposal per lead ("here's what I'd build for you")
