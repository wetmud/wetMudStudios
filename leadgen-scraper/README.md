# leadgen-scraper

Python CLI that fetches local business data via Google Places API, scrapes individual business websites for signals, scores leads by digital presence gaps, and writes them to a shared SQLite database.

## Setup

```bash
pip install -r requirements.txt
export GOOGLE_PLACES_API_KEY=your_key_here
```

## Usage

```bash
python scrape.py --city Burlington --type restaurant
python scrape.py --city Hamilton --type salon --limit 50
```

## How It Works

1. **Places API** — Text Search finds businesses; Place Details fetches name, address, phone, website, reviews.
2. **Detector** — HTTP request to each website detects platform (Wix, Squarespace, WordPress, etc.) and SSL status. SSRF-safe: loopback and RFC-1918 addresses are blocked.
3. **Scorer** — Assigns a 0–100 score based on digital presence gaps:
   - No website: +40
   - No Google listing: +30
   - Template site (Wix/Squarespace/Weebly): +20
   - Few or old reviews: +10
   - Niche match: +15
   - No SSL: +10
4. **DB** — Deduplicates by normalized name + city + phone, then inserts into `leads.db` with WAL mode.

## Output

```
Scrape complete -- 12 new leads added, 3 skipped (duplicates).
```

Leads are written to `leads.db` (one level up from this directory, shared with the CRM).

## Tests

```bash
python -m pytest tests/ -v
```

27 tests covering db, scorer, detector, and places modules.
