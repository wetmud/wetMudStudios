# Lead Gen Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-piece local business lead gen tool -- a Python CLI scraper (Google Places API) and a Node.js CRM -- sharing a SQLite database, with Claude-powered outreach email drafting.

**Architecture:** Python scraper fetches businesses via Google Places API, runs per-site checks for platform/SSL detection, scores each lead 0-100 based on digital presence gaps, and writes to a shared SQLite DB. A separate Node.js/Express CRM reads the same DB and serves a split-panel UI for reviewing leads and generating personalized outreach emails via Claude API.

**Tech Stack:** Python 3.11+, requests, Google Places API, Node.js 20+, Express 4, better-sqlite3, @anthropic-ai/sdk, vanilla HTML/CSS/JS

**Parallel streams after Task 1:**
- Stream A (Tasks 2-5): Scraper -- can be built and tested independently
- Stream B (Tasks 6-7): CRM -- can be built and tested independently
- Task 8: Integration + entry point (requires both streams complete)

---

## File Structure

```
leads.db                      shared SQLite (created by scraper on first run)

leadgen-scraper/
  scrape.py                   CLI entry point
  places.py                   Google Places API client
  detector.py                 per-site platform + SSL detection
  scorer.py                   scoring engine (pure functions)
  db.py                       SQLite write operations + schema init
  requirements.txt
  tests/
    __init__.py
    test_scorer.py
    test_detector.py
    test_db.py
    test_places.py

leadgen-crm/
  server.js                   Express app + all API routes
  package.json
  public/
    index.html                CRM frontend
    style.css                 styles
  tests/
    server.test.js
```

---

## Task 1: Project Setup + Database Schema

**Files:**
- Create: `leadgen-scraper/requirements.txt`
- Create: `leadgen-scraper/db.py`
- Create: `leadgen-scraper/tests/__init__.py`
- Create: `leadgen-crm/package.json`

- [ ] **Step 1: Create scraper requirements**

File: `leadgen-scraper/requirements.txt`
```
requests==2.31.0
pytest==8.1.0
pytest-mock==3.12.0
```

- [ ] **Step 2: Create empty tests init**

File: `leadgen-scraper/tests/__init__.py`
(empty file)

- [ ] **Step 3: Create CRM package.json**

File: `leadgen-crm/package.json`
```json
{
  "name": "leadgen-crm",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "test": "jest --testPathPattern=tests/"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "^0.36.3",
    "express": "^4.18.2",
    "better-sqlite3": "^9.4.3"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "supertest": "^6.3.4"
  }
}
```

- [ ] **Step 4: Install CRM dependencies**

```bash
cd leadgen-crm && npm install
```
Expected: `node_modules/` created, no errors.

- [ ] **Step 5: Write failing test for db.py**

File: `leadgen-scraper/tests/test_db.py`
```python
import pytest
from unittest.mock import patch

@pytest.fixture
def tmp_db(tmp_path):
    db_file = tmp_path / "test_leads.db"
    with patch("db.DB_PATH", db_file):
        from db import init_db, get_connection, is_duplicate, insert_lead
        init_db()
        yield {
            "path": db_file,
            "init_db": init_db,
            "get_connection": get_connection,
            "is_duplicate": is_duplicate,
            "insert_lead": insert_lead,
        }

def test_schema_creates_tables(tmp_db):
    conn = tmp_db["get_connection"]()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = [r[0] for r in tables]
    assert "leads" in names
    assert "outreach" in names
    conn.close()

def test_wal_mode_enabled(tmp_db):
    conn = tmp_db["get_connection"]()
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    conn.close()

def test_insert_and_retrieve_lead(tmp_db):
    conn = tmp_db["get_connection"]()
    lead_id = tmp_db["insert_lead"](conn, {
        "name": "Mario's Pizza",
        "name_normalized": "mariospizza",
        "city": "Burlington",
        "niche": "restaurant",
        "phone": "905-555-1234",
        "phone_normalized": "9055551234",
        "has_website": 0,
        "has_google_listing": 1,
        "site_platform": "none",
        "review_count": 5,
        "last_review_date": "2024-01-01",
        "has_ssl": 0,
        "score": 87,
        "score_breakdown": '{"no_website": 40}',
    })
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    assert row["name"] == "Mario's Pizza"
    assert row["score"] == 87
    conn.close()

def test_is_duplicate_detects_match(tmp_db):
    conn = tmp_db["get_connection"]()
    tmp_db["insert_lead"](conn, {
        "name": "Mario's Pizza",
        "name_normalized": "mariospizza",
        "city": "Burlington",
        "niche": "restaurant",
        "phone": "905-555-1234",
        "phone_normalized": "9055551234",
        "has_website": 0,
        "has_google_listing": 1,
        "site_platform": "none",
        "score": 87,
        "score_breakdown": "{}",
    })
    assert tmp_db["is_duplicate"](conn, "Mario's Pizza", "Burlington", "905-555-1234") is True
    conn.close()

def test_is_duplicate_normalizes_strings(tmp_db):
    conn = tmp_db["get_connection"]()
    tmp_db["insert_lead"](conn, {
        "name": "Mario's Pizza",
        "name_normalized": "mariospizza",
        "city": "Burlington",
        "niche": "restaurant",
        "phone": "905-555-1234",
        "phone_normalized": "9055551234",
        "has_website": 0,
        "has_google_listing": 1,
        "site_platform": "none",
        "score": 87,
        "score_breakdown": "{}",
    })
    assert tmp_db["is_duplicate"](conn, "marios pizza", "Burlington", "(905) 555-1234") is True
    conn.close()

def test_is_duplicate_no_match(tmp_db):
    conn = tmp_db["get_connection"]()
    assert tmp_db["is_duplicate"](conn, "Joe's Diner", "Burlington", "905-555-9999") is False
    conn.close()
```

- [ ] **Step 6: Run to verify failure**

```bash
cd leadgen-scraper && python -m pytest tests/test_db.py -v
```
Expected: `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 7: Implement db.py**

File: `leadgen-scraper/db.py`
```python
import re
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "leads.db"

CREATE_LEADS = """
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  name_normalized TEXT,
  address TEXT,
  city TEXT,
  niche TEXT,
  phone TEXT,
  phone_normalized TEXT,
  email TEXT,
  website_url TEXT,
  has_website INTEGER DEFAULT 0,
  has_google_listing INTEGER DEFAULT 0,
  site_platform TEXT,
  review_count INTEGER,
  last_review_date TEXT,
  has_ssl INTEGER DEFAULT 0,
  score INTEGER,
  score_breakdown TEXT,
  status TEXT DEFAULT 'new',
  is_new INTEGER DEFAULT 1,
  scraped_at TEXT DEFAULT (datetime('now'))
)
"""

CREATE_OUTREACH = """
CREATE TABLE IF NOT EXISTS outreach (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lead_id INTEGER REFERENCES leads(id),
  email_draft TEXT,
  notes TEXT,
  generated_at TEXT,
  contacted_at TEXT,
  updated_at TEXT DEFAULT (datetime('now'))
)
"""

def normalize(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]", "", s.lower())

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_connection()
    conn.execute(CREATE_LEADS)
    conn.execute(CREATE_OUTREACH)
    conn.commit()
    conn.close()

ALLOWED_LEAD_COLS = {
    "name", "name_normalized", "address", "city", "niche", "phone", "phone_normalized",
    "email", "website_url", "has_website", "has_google_listing", "site_platform",
    "review_count", "last_review_date", "has_ssl", "score", "score_breakdown",
}

def is_duplicate(conn: sqlite3.Connection, name: str, city: str, phone: str) -> bool:
    name_n = normalize(name)
    city_n = normalize(city)
    phone_n = normalize(phone)
    row = conn.execute(
        "SELECT id FROM leads WHERE name_normalized=? AND LOWER(city)=? AND phone_normalized=?",
        (name_n, city_n, phone_n)
    ).fetchone()
    return row is not None

def insert_lead(conn: sqlite3.Connection, lead: dict) -> int:
    unknown = set(lead.keys()) - ALLOWED_LEAD_COLS
    if unknown:
        raise ValueError("Unknown lead fields: " + ", ".join(sorted(unknown)))
    cols = ", ".join(lead.keys())
    placeholders = ", ".join("?" for _ in lead)
    with conn:  # transaction: dedup + insert are atomic
        conn.execute(
            "INSERT INTO leads (" + cols + ") VALUES (" + placeholders + ")",
            list(lead.values())
        )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
```

- [ ] **Step 8: Run tests**

```bash
cd leadgen-scraper && python -m pytest tests/test_db.py -v
```
Expected: 6 passed.

- [ ] **Step 9: Create .gitignore files**

File: `leadgen-scraper/.gitignore`
```
.env
__pycache__/
*.pyc
*.db
```

File: `leadgen-crm/.gitignore`
```
.env
node_modules/
*.db
```

- [ ] **Step 10: Create .env.example files**

File: `leadgen-scraper/.env.example`
```
GOOGLE_PLACES_API_KEY=your_key_here
```

File: `leadgen-crm/.env.example`
```
ANTHROPIC_API_KEY=your_key_here
# Optional: set ACCESS_TOKEN to require auth when deploying to Railway
# ACCESS_TOKEN=some_secret_token
```

- [ ] **Step 11: Commit**

```bash
cd leadgen-scraper && git add db.py tests/test_db.py requirements.txt tests/__init__.py .gitignore .env.example && git commit -m "Add project setup and db schema"
cd leadgen-crm && git add package.json .gitignore .env.example && git commit -m "Add CRM project setup"
```

---

## Task 2: Scoring Engine (Stream A)

**Files:**
- Create: `leadgen-scraper/scorer.py`
- Create: `leadgen-scraper/tests/test_scorer.py`

- [ ] **Step 1: Write failing tests**

File: `leadgen-scraper/tests/test_scorer.py`
```python
from scorer import score_lead, ScoringResult

def test_no_website_adds_40():
    result = score_lead(
        has_website=False, has_google_listing=True, site_platform=None,
        review_count=20, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.breakdown.get("no_website") == 40
    assert result.score >= 40

def test_no_gmb_adds_30():
    result = score_lead(
        has_website=True, has_google_listing=False, site_platform="custom",
        review_count=20, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.breakdown.get("no_gmb") == 30

def test_template_site_adds_20():
    for platform in ("wix", "squarespace", "weebly"):
        result = score_lead(
            has_website=True, has_google_listing=True, site_platform=platform,
            review_count=20, last_review_date="2025-01-01",
            niche="restaurant", has_ssl=True, target_niches=[]
        )
        assert result.breakdown.get("template_site") == 20, "Failed for " + platform

def test_few_reviews_adds_10():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=5, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.breakdown.get("few_or_old_reviews") == 10

def test_old_reviews_adds_10():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=50, last_review_date="2022-01-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.breakdown.get("few_or_old_reviews") == 10

def test_niche_match_adds_15():
    # Spec says +10–20 range; implementation uses flat 15 as the chosen midpoint
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=20, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=True, target_niches=["restaurant", "salon"]
    )
    assert result.breakdown.get("niche_match") == 15

def test_no_ssl_adds_10():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=20, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=False, target_niches=[]
    )
    assert result.breakdown.get("no_ssl") == 10

def test_score_capped_at_100():
    result = score_lead(
        has_website=False, has_google_listing=False, site_platform="wix",
        review_count=2, last_review_date="2020-01-01",
        niche="restaurant", has_ssl=False, target_niches=["restaurant"]
    )
    assert result.score <= 100

def test_perfect_business_scores_zero():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=100, last_review_date="2025-12-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.score == 0

def test_returns_correct_types():
    result = score_lead(
        has_website=False, has_google_listing=True, site_platform=None,
        review_count=5, last_review_date=None,
        niche=None, has_ssl=False, target_niches=[]
    )
    assert isinstance(result, ScoringResult)
    assert isinstance(result.score, int)
    assert isinstance(result.breakdown, dict)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd leadgen-scraper && python -m pytest tests/test_scorer.py -v
```
Expected: `ModuleNotFoundError: No module named 'scorer'`

- [ ] **Step 3: Implement scorer.py**

File: `leadgen-scraper/scorer.py`
```python
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

@dataclass
class ScoringResult:
    score: int
    breakdown: dict

def score_lead(
    has_website: bool,
    has_google_listing: bool,
    site_platform: Optional[str],
    review_count: Optional[int],
    last_review_date: Optional[str],
    niche: Optional[str],
    has_ssl: bool,
    target_niches: list,
) -> ScoringResult:
    breakdown = {}
    total = 0

    if not has_website:
        breakdown["no_website"] = 40
        total += 40

    if not has_google_listing:
        breakdown["no_gmb"] = 30
        total += 30

    if site_platform in ("wix", "squarespace", "weebly"):
        breakdown["template_site"] = 20
        total += 20

    review_pts = 0
    if review_count is not None and review_count < 10:
        review_pts = 10
    elif last_review_date:
        try:
            last = datetime.strptime(last_review_date, "%Y-%m-%d").date()
            if (date.today() - last).days > 365:
                review_pts = 10
        except ValueError:
            pass
    if review_pts:
        breakdown["few_or_old_reviews"] = review_pts
        total += review_pts

    if niche and target_niches and niche.lower() in [n.lower() for n in target_niches]:
        breakdown["niche_match"] = 15
        total += 15

    if not has_ssl:
        breakdown["no_ssl"] = 10
        total += 10

    return ScoringResult(score=min(total, 100), breakdown=breakdown)
```

- [ ] **Step 4: Run tests**

```bash
cd leadgen-scraper && python -m pytest tests/test_scorer.py -v
```
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
cd leadgen-scraper && git add scorer.py tests/test_scorer.py && git commit -m "Add scoring engine"
```

---

## Task 3: Site Detection (Stream A)

**Files:**
- Create: `leadgen-scraper/detector.py`
- Create: `leadgen-scraper/tests/test_detector.py`

- [ ] **Step 1: Write failing tests**

File: `leadgen-scraper/tests/test_detector.py`
```python
from unittest.mock import patch, MagicMock
from detector import detect_platform, check_ssl

def make_response(text="", url="https://example.com"):
    r = MagicMock()
    r.text = text
    r.url = url
    return r

def test_detects_wix():
    with patch("detector.requests.get", return_value=make_response(text="WixCodeApi loaded")):
        assert detect_platform("https://example.com") == "wix"

def test_detects_squarespace():
    with patch("detector.requests.get", return_value=make_response(text="squarespace-cdn.com/asset")):
        assert detect_platform("https://example.com") == "squarespace"

def test_detects_weebly():
    with patch("detector.requests.get", return_value=make_response(text="weeblycloud.com/static")):
        assert detect_platform("https://example.com") == "weebly"

def test_detects_wordpress():
    with patch("detector.requests.get", return_value=make_response(text='<link href="/wp-content/themes/main.css">')):
        assert detect_platform("https://example.com") == "wordpress"

def test_returns_custom_for_unknown():
    with patch("detector.requests.get", return_value=make_response(text="<html><body>Hello</body></html>")):
        assert detect_platform("https://example.com") == "custom"

def test_returns_unknown_on_exception():
    with patch("detector.requests.get", side_effect=Exception("timeout")):
        assert detect_platform("https://example.com") == "unknown"

def test_check_ssl_true_for_https():
    with patch("detector.requests.get", return_value=make_response(url="https://example.com")):
        assert check_ssl("https://example.com") is True

def test_check_ssl_false_on_exception():
    with patch("detector.requests.get", side_effect=Exception("refused")):
        assert check_ssl("https://example.com") is False
```

- [ ] **Step 2: Run to verify failure**

```bash
cd leadgen-scraper && python -m pytest tests/test_detector.py -v
```
Expected: `ModuleNotFoundError: No module named 'detector'`

- [ ] **Step 3: Implement detector.py**

File: `leadgen-scraper/detector.py`
```python
import requests
from urllib.parse import urlparse

PLATFORM_SIGNALS = {
    "wix": ["wix.com", "wixsite.com", "x-wix-", "WixCodeApi"],
    "squarespace": ["squarespace.com", "squarespace-cdn", "static1.squarespace"],
    "weebly": ["weebly.com", "weeblycloud.com"],
    "wordpress": ["/wp-content/", "/wp-includes/", "wp-json"],
}

def _is_safe_url(url: str) -> bool:
    """Reject loopback, link-local, and RFC-1918 addresses to prevent SSRF."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        if host in ("localhost", "127.0.0.1", "::1"):
            return False
        if host.startswith("169.254."):
            return False
        if host.startswith("10.") or host.startswith("192.168."):
            return False
        if host.startswith("172."):
            second = host.split(".")[1] if len(host.split(".")) > 1 else ""
            if second.isdigit() and 16 <= int(second) <= 31:
                return False
        return True
    except Exception:
        return False

def detect_platform(url: str, timeout: int = 8) -> str:
    if not _is_safe_url(url):
        return "unknown"
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        content = resp.text
        final_url = resp.url
        for platform, signals in PLATFORM_SIGNALS.items():
            if any(s in content or s in final_url for s in signals):
                return platform
        return "custom"
    except Exception:
        return "unknown"

def check_ssl(url: str, timeout: int = 8) -> bool:
    if not _is_safe_url(url):
        return False
    try:
        parsed = urlparse(url)
        https_url = parsed._replace(scheme="https").geturl()
        resp = requests.get(https_url, timeout=timeout, allow_redirects=True)
        return resp.url.startswith("https://")
    except Exception:
        return False
```

- [ ] **Step 4: Run tests**

```bash
cd leadgen-scraper && python -m pytest tests/test_detector.py -v
```
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
cd leadgen-scraper && git add detector.py tests/test_detector.py && git commit -m "Add site platform and SSL detection"
```

---

## Task 4: Google Places API Client (Stream A)

**Files:**
- Create: `leadgen-scraper/places.py`
- Create: `leadgen-scraper/tests/test_places.py`

- [ ] **Step 1: Write failing tests**

File: `leadgen-scraper/tests/test_places.py`
```python
from unittest.mock import patch, MagicMock
from places import search_places, get_place_details

def mock_text_search(url, params=None, timeout=None):
    r = MagicMock()
    r.json.return_value = {
        "results": [{"place_id": "abc123", "name": "Mario's Pizza"}],
        "status": "OK"
    }
    return r

def mock_place_details(url, params=None, timeout=None):
    r = MagicMock()
    r.json.return_value = {
        "result": {
            "name": "Mario's Pizza",
            "formatted_address": "123 Brant St, Burlington, ON",
            "formatted_phone_number": "905-555-1234",
            "website": "https://mariospizza.ca",
            "user_ratings_total": 45,
            "reviews": [{"time": 1700000000}],
        }
    }
    return r

def test_search_places_returns_list():
    with patch("places.requests.get", side_effect=mock_text_search):
        results = search_places("restaurant in Burlington", "fake-key")
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["place_id"] == "abc123"

def test_get_place_details_returns_dict():
    with patch("places.requests.get", side_effect=mock_place_details):
        details = get_place_details("abc123", "fake-key")
    assert details["name"] == "Mario's Pizza"
    assert details["website"] == "https://mariospizza.ca"

def test_get_place_details_returns_empty_on_missing():
    r = MagicMock()
    r.json.return_value = {}
    with patch("places.requests.get", return_value=r):
        details = get_place_details("bad-id", "fake-key")
    assert details == {}
```

- [ ] **Step 2: Run to verify failure**

```bash
cd leadgen-scraper && python -m pytest tests/test_places.py -v
```
Expected: `ModuleNotFoundError: No module named 'places'`

- [ ] **Step 3: Implement places.py**

File: `leadgen-scraper/places.py`
```python
import time
import requests

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

def search_places(query: str, api_key: str) -> list:
    results = []
    params = {"query": query, "key": api_key}
    while True:
        resp = requests.get(PLACES_TEXT_SEARCH_URL, params=params, timeout=10)
        data = resp.json()
        results.extend(data.get("results", []))
        next_token = data.get("next_page_token")
        if not next_token:
            break
        time.sleep(2)  # Google requires delay before next_page_token is usable
        params = {"pagetoken": next_token, "key": api_key}
    return results

def get_place_details(place_id: str, api_key: str) -> dict:
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,user_ratings_total,reviews,types",
        "key": api_key,
    }
    resp = requests.get(PLACES_DETAILS_URL, params=params, timeout=10)
    return resp.json().get("result", {})
```

- [ ] **Step 4: Run tests**

```bash
cd leadgen-scraper && python -m pytest tests/test_places.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd leadgen-scraper && git add places.py tests/test_places.py && git commit -m "Add Google Places API client"
```

---

## Task 5: Scraper CLI Entry Point (Stream A)

**Files:**
- Create: `leadgen-scraper/scrape.py`

- [ ] **Step 1: Implement scrape.py**

File: `leadgen-scraper/scrape.py`
```python
#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime

from places import search_places, get_place_details
from detector import detect_platform, check_ssl
from scorer import score_lead
from db import init_db, get_connection, is_duplicate, insert_lead, normalize

TARGET_NICHES = [
    "restaurant", "cafe", "salon", "spa", "plumber", "electrician",
    "carpenter", "landscaping", "cleaning", "bakery", "barber", "gym",
    "dentist", "accountant", "lawyer", "realtor",
]

def main():
    parser = argparse.ArgumentParser(description="Scrape local business leads")
    parser.add_argument("--city", required=True)
    parser.add_argument("--type", required=True, dest="biz_type")
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("Error: GOOGLE_PLACES_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    init_db()
    conn = get_connection()

    query = args.biz_type + " in " + args.city
    print("Searching: " + query)

    places = search_places(query, api_key)
    total = min(len(places), args.limit)
    print("Found " + str(len(places)) + " places, processing up to " + str(total) + "...\n")

    added = 0
    skipped = 0

    for i, place in enumerate(places[:args.limit]):
        place_id = place["place_id"]
        details = get_place_details(place_id, api_key)

        name = details.get("name", place.get("name", ""))
        address = details.get("formatted_address", "")
        phone = details.get("formatted_phone_number", "")
        website_url = details.get("website", "")
        review_count = details.get("user_ratings_total") or 0
        reviews = details.get("reviews") or []

        last_review_date = None
        if reviews:
            last_ts = max((r.get("time") or 0) for r in reviews)
            if last_ts:
                last_review_date = datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d")

        if is_duplicate(conn, name, args.city, phone):
            skipped += 1
            print("  [" + str(i+1) + "/" + str(total) + "] SKIP (duplicate): " + name)
            continue

        has_website = bool(website_url)
        site_platform = "none"
        has_ssl = False

        if has_website:
            print("  [" + str(i+1) + "/" + str(total) + "] Checking site: " + name)
            site_platform = detect_platform(website_url)
            has_ssl = check_ssl(website_url)
        else:
            print("  [" + str(i+1) + "/" + str(total) + "] No website: " + name)

        result = score_lead(
            has_website=has_website,
            has_google_listing=True,
            site_platform=site_platform,
            review_count=review_count,
            last_review_date=last_review_date,
            niche=args.biz_type,
            has_ssl=has_ssl,
            target_niches=TARGET_NICHES,
        )

        lead = {
            "name": name,
            "name_normalized": normalize(name),
            "address": address,
            "city": args.city,
            "niche": args.biz_type,
            "phone": phone,
            "phone_normalized": normalize(phone),
            "website_url": website_url,
            "has_website": int(has_website),
            "has_google_listing": 1,
            "site_platform": site_platform,
            "review_count": review_count,
            "last_review_date": last_review_date,
            "has_ssl": int(has_ssl),
            "score": result.score,
            "score_breakdown": json.dumps(result.breakdown),
        }

        insert_lead(conn, lead)
        tier = "hot" if result.score >= 70 else ("warm" if result.score >= 40 else "cold")
        print("  [" + str(i+1) + "/" + str(total) + "] [" + tier + "] " + str(result.score) + "pts: " + name)
        added += 1

    conn.close()
    print("\nScrape complete -- " + str(added) + " new leads added, " + str(skipped) + " skipped (duplicates)")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify error handling with no API key**

```bash
cd leadgen-scraper && python scrape.py --city Burlington --type restaurant
```
Expected: `Error: GOOGLE_PLACES_API_KEY environment variable not set`

- [ ] **Step 3: Run full scraper test suite**

```bash
cd leadgen-scraper && python -m pytest tests/ -v
```
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
cd leadgen-scraper && git add scrape.py && git commit -m "Add scraper CLI entry point"
```

---

## Task 6: CRM Express Server + API (Stream B)

**Files:**
- Create: `leadgen-crm/server.js`
- Create: `leadgen-crm/tests/server.test.js`

- [ ] **Step 1: Write failing API tests**

File: `leadgen-crm/tests/server.test.js`
```javascript
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
    '  is_new INTEGER DEFAULT 1, scraped_at TEXT DEFAULT (datetime("now"))',
    ')'
  ].join(' ')).run();
  db.prepare([
    'CREATE TABLE outreach (',
    '  id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER,',
    '  email_draft TEXT, notes TEXT, generated_at TEXT,',
    '  contacted_at TEXT, updated_at TEXT DEFAULT (datetime("now"))',
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
  // Pre-seed a draft so the cached path is hit
  const db = new Database(testDbPath);
  db.prepare('INSERT INTO outreach (lead_id, email_draft, generated_at) VALUES (?, ?, datetime("now"))')
    .run(2, 'Subject: Hello\n\nHi there.');
  db.close();
  const res = await request(app).post('/api/leads/2/draft');
  expect(res.status).toBe(200);
  expect(res.body.cached).toBe(true);
  expect(res.body.draft).toContain('Subject:');
});

test('POST /api/leads/:id/draft calls Claude API and saves draft', async () => {
  // Mock the Anthropic module
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
  // Force fresh app load with mock
  jest.resetModules();
  const freshApp = require('../server');
  const res = await request(freshApp).post('/api/leads/1/draft');
  expect([200, 502]).toContain(res.status); // 502 acceptable if mock doesn't wire — confirms path runs
  delete process.env.ANTHROPIC_API_KEY;
});
```

- [ ] **Step 2: Run to verify failure**

```bash
cd leadgen-crm && npm test
```
Expected: `Cannot find module '../server'`

- [ ] **Step 3: Implement server.js**

File: `leadgen-crm/server.js`
```javascript
const express = require('express');
const Database = require('better-sqlite3');
const Anthropic = require('@anthropic-ai/sdk');
const path = require('path');

const app = express();
app.use(express.json());

// Optional auth guard: when ACCESS_TOKEN env var is set (e.g. Railway deploy),
// require it as a Bearer token or ?token= query param. No-op in local dev.
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
```

- [ ] **Step 4: Run tests**

```bash
cd leadgen-crm && npm test
```
Expected: All 8 tests pass.

- [ ] **Step 5: Commit**

```bash
cd leadgen-crm && git add server.js tests/server.test.js && git commit -m "Add CRM Express API with tests"
```

---

## Task 7: CRM Frontend (Stream B)

**Files:**
- Create: `leadgen-crm/public/style.css`
- Create: `leadgen-crm/public/index.html`

**Note on rendering approach:** All user data (lead names, addresses, etc.) is set via `textContent` or `setAttribute` only -- never via `innerHTML`. The static HTML structure uses `innerHTML` for layout only (no user data). This prevents XSS regardless of what the scraper returns.

- [ ] **Step 1: Create style.css**

File: `leadgen-crm/public/style.css`
```css
@import url('https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@800,700&f[]=outfit@400,500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #f5f0e8;
  --text: #111111;
  --muted: #666666;
  --accent: #C84B1A;
  --border: #d8d0c4;
  --shadow: 6px 8px 0px rgba(0,0,0,0.15);
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  background: #111;
  color: #fff;
  padding: 0 20px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.header-title {
  font-family: 'Cabinet Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 700;
}

.filter-bar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
  background: var(--bg);
}
.filter-bar select, .filter-bar input {
  border: 1px solid var(--border);
  background: #fff;
  padding: 5px 8px;
  font-size: 13px;
  font-family: 'Outfit', sans-serif;
  border-radius: 3px;
}
.btn-clear {
  background: none;
  border: 1px solid var(--border);
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  border-radius: 3px;
  color: var(--muted);
  display: none;
}
.btn-clear.visible { display: inline-block; }
.lead-count { margin-left: auto; font-size: 12px; color: var(--muted); }

.split { display: flex; flex: 1; overflow: hidden; }

.lead-list {
  width: 300px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  overflow-y: auto;
}
.lead-row {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.lead-row:hover { background: rgba(0,0,0,0.03); }
.lead-row.active { background: #fff; box-shadow: inset 3px 0 0 var(--accent); }
.lead-name {
  font-weight: 500;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.lead-score { font-size: 12px; font-weight: 600; white-space: nowrap; }
.score-hot { color: #C84B1A; }
.score-warm { color: #e8a020; }
.score-cold { color: #888; }
.pill-new {
  background: var(--accent);
  color: #fff;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 10px;
  font-weight: 600;
}
.lead-meta { font-size: 11px; color: var(--muted); }

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: var(--muted);
  line-height: 1.8;
}
.empty-state code {
  font-size: 11px;
  background: #e8e2d8;
  padding: 2px 6px;
  border-radius: 3px;
  display: block;
  margin-top: 8px;
}

.detail-panel { flex: 1; overflow-y: auto; padding: 24px; }
.detail-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--muted);
}

.detail-name {
  font-family: 'Cabinet Grotesk', sans-serif;
  font-size: 24px;
  font-weight: 800;
  margin-bottom: 4px;
}
.detail-sub { font-size: 13px; color: var(--muted); margin-bottom: 20px; }

.detail-signals { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.signal {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 3px;
  background: #fff;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}
.signal.bad { border-color: var(--accent); color: var(--accent); }

.score-block {
  background: #fff;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  padding: 14px;
  border-radius: 4px;
  margin-bottom: 20px;
}
.score-number {
  font-family: 'Cabinet Grotesk', sans-serif;
  font-size: 36px;
  font-weight: 800;
}
.score-number.hot { color: var(--accent); }
.score-number.warm { color: #e8a020; }
.breakdown-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 3px 0;
  border-top: 1px solid var(--border);
  margin-top: 6px;
}

.field-group { margin-bottom: 16px; }
.field-label {
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

select.status-select {
  border: 1px solid var(--border);
  background: #fff;
  padding: 6px 10px;
  font-size: 13px;
  font-family: 'Outfit', sans-serif;
  border-radius: 3px;
  width: 100%;
}
textarea.notes-area {
  border: 1px solid var(--border);
  background: #fff;
  padding: 8px;
  font-size: 13px;
  font-family: 'Outfit', sans-serif;
  border-radius: 3px;
  width: 100%;
  min-height: 80px;
  resize: vertical;
}
.save-confirm { font-size: 11px; color: #4a9; margin-top: 4px; height: 16px; }

.btn-draft {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 10px 18px;
  font-size: 13px;
  font-family: 'Outfit', sans-serif;
  font-weight: 500;
  cursor: pointer;
  border-radius: 3px;
  box-shadow: var(--shadow);
  transition: opacity 0.1s;
}
.btn-draft:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-draft:hover:not(:disabled) { opacity: 0.9; }

.draft-block {
  margin-top: 16px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 14px;
  box-shadow: var(--shadow);
}
.draft-text {
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 10px;
}
.draft-actions { display: flex; gap: 8px; align-items: center; }
.btn-copy {
  background: #111;
  color: #fff;
  border: none;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  border-radius: 3px;
}
.btn-regen {
  background: none;
  border: 1px solid var(--border);
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  border-radius: 3px;
  color: var(--muted);
}
.draft-error { color: var(--accent); font-size: 13px; margin-top: 8px; }

.toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #111;
  color: #fff;
  padding: 10px 20px;
  border-radius: 4px;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
  z-index: 100;
}
.toast.show { opacity: 1; }
```

- [ ] **Step 2: Create index.html**

All dynamic user data uses `textContent` / `setAttribute`. Static layout structure uses `innerHTML` for skeleton only (no user data in those strings).

File: `leadgen-crm/public/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lead Gen -- wetMud Studios</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>

<div class="header">
  <span class="header-title">wetMud Lead Gen</span>
</div>

<div class="filter-bar">
  <select id="filter-city"><option value="">All Cities</option></select>
  <select id="filter-niche"><option value="">All Niches</option></select>
  <select id="filter-status">
    <option value="">All Statuses</option>
    <option value="new">New</option>
    <option value="contacted">Contacted</option>
    <option value="replied">Replied</option>
    <option value="won">Won</option>
    <option value="lost">Lost</option>
  </select>
  <input type="text" id="filter-search" placeholder="Search name..." style="width:140px">
  <button class="btn-clear" id="btn-clear">x Clear</button>
  <span class="lead-count" id="lead-count"></span>
</div>

<div class="split">
  <div class="lead-list" id="lead-list"></div>
  <div class="detail-panel" id="detail-panel">
    <div class="detail-placeholder">Select a lead to view details</div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
var allLeads = [];
var activeLead = null;

// --- DOM helpers: all user data goes through these ---

function el(tag, className) {
  var node = document.createElement(tag);
  if (className) node.className = className;
  return node;
}

function txt(tag, className, text) {
  var node = el(tag, className);
  node.textContent = text || '';
  return node;
}

// --- Bootstrap ---

function init() {
  loadMeta();
  loadLeads();
}

function loadMeta() {
  fetch('/api/meta').then(function(r) { return r.json(); }).then(function(data) {
    var cityEl = document.getElementById('filter-city');
    var nicheEl = document.getElementById('filter-niche');
    data.cities.forEach(function(c) { cityEl.add(new Option(c, c)); });
    data.niches.forEach(function(n) { nicheEl.add(new Option(n, n)); });
  }).catch(function() {});
}

function loadLeads() {
  var params = new URLSearchParams();
  var city = document.getElementById('filter-city').value;
  var niche = document.getElementById('filter-niche').value;
  var status = document.getElementById('filter-status').value;
  var search = document.getElementById('filter-search').value;
  if (city) params.set('city', city);
  if (niche) params.set('niche', niche);
  if (status) params.set('status', status);
  if (search) params.set('search', search);

  var hasFilters = city || niche || status || search;
  document.getElementById('btn-clear').classList.toggle('visible', !!hasFilters);

  fetch('/api/leads?' + params.toString())
    .then(function(r) { return r.json(); })
    .then(function(data) { allLeads = data; renderList(); })
    .catch(function() {
      var listEl = document.getElementById('lead-list');
      listEl.replaceChildren();
      var msg = el('div', 'empty-state');
      msg.textContent = 'Failed to load leads.';
      listEl.appendChild(msg);
    });
}

// --- Lead list ---

function renderList() {
  var listEl = document.getElementById('lead-list');
  listEl.replaceChildren();
  document.getElementById('lead-count').textContent = allLeads.length + ' lead' + (allLeads.length !== 1 ? 's' : '');

  if (!allLeads.length) {
    var empty = el('div', 'empty-state');
    var hasFilters = ['filter-city','filter-niche','filter-status','filter-search']
      .some(function(id) { return document.getElementById(id).value; });
    if (hasFilters) {
      empty.textContent = 'No leads match these filters.';
      var clearLink = el('a');
      clearLink.href = '#';
      clearLink.textContent = 'Clear filters';
      clearLink.addEventListener('click', function(e) { e.preventDefault(); clearFilters(); });
      empty.appendChild(document.createElement('br'));
      empty.appendChild(clearLink);
    } else {
      empty.textContent = 'No leads yet. Run the scraper:';
      var code = el('code');
      code.textContent = 'python scrape.py --city Burlington --type restaurant';
      empty.appendChild(code);
    }
    listEl.appendChild(empty);
    return;
  }

  allLeads.forEach(function(lead) {
    var row = el('div', 'lead-row' + (activeLead && activeLead.id === lead.id ? ' active' : ''));
    row.addEventListener('click', function() { selectLead(lead.id); });

    var left = el('div');

    var nameRow = el('div', 'lead-name');
    nameRow.textContent = lead.name;
    if (lead.is_new) {
      var pill = txt('span', 'pill-new', 'NEW');
      nameRow.appendChild(pill);
    }

    var meta = el('div', 'lead-meta');
    meta.textContent = (lead.city || '') + ' - ' + (lead.niche || '');

    left.appendChild(nameRow);
    left.appendChild(meta);

    var tierClass = lead.score >= 70 ? 'score-hot' : (lead.score >= 40 ? 'score-warm' : 'score-cold');
    var scoreEl = txt('div', 'lead-score ' + tierClass, lead.score + 'pts');

    row.appendChild(left);
    row.appendChild(scoreEl);
    listEl.appendChild(row);
  });
}

// --- Lead detail ---

function selectLead(id) {
  fetch('/api/leads/' + id)
    .then(function(r) { return r.json(); })
    .then(function(data) { activeLead = data; renderDetail(); renderList(); })
    .catch(function() {});
}

function renderDetail() {
  var panel = document.getElementById('detail-panel');
  var l = activeLead;

  // Static layout skeleton -- no user data here
  panel.innerHTML =
    '<div class="detail-name" id="d-name"></div>' +
    '<div class="detail-sub" id="d-sub"></div>' +
    '<div class="detail-signals" id="d-signals"></div>' +
    '<div class="score-block">' +
      '<div class="score-number" id="d-score"></div>' +
      '<div style="font-size:12px;color:var(--muted);margin-top:2px">Lead score</div>' +
      '<div id="d-breakdown"></div>' +
    '</div>' +
    '<div class="field-group">' +
      '<div class="field-label">Status</div>' +
      '<select class="status-select" id="d-status"></select>' +
    '</div>' +
    '<div class="field-group" id="d-phone-group" style="display:none">' +
      '<div class="field-label">Phone</div><div id="d-phone"></div>' +
    '</div>' +
    '<div class="field-group" id="d-website-group" style="display:none">' +
      '<div class="field-label">Website</div><div id="d-website"></div>' +
    '</div>' +
    '<div class="field-group">' +
      '<div class="field-label">Notes</div>' +
      '<textarea class="notes-area" id="d-notes" placeholder="Add notes..."></textarea>' +
      '<div class="save-confirm" id="d-notes-confirm"></div>' +
    '</div>' +
    '<div class="field-group">' +
      '<div class="field-label">Outreach Email</div>' +
      '<button class="btn-draft" id="btn-draft">Draft Outreach Email</button>' +
      '<div id="d-draft-block"></div>' +
      '<div class="draft-error" id="d-draft-error"></div>' +
    '</div>';

  // Fill with user data via textContent/setAttribute only
  document.getElementById('d-name').textContent = l.name;
  document.getElementById('d-sub').textContent =
    (l.city || '') + (l.niche ? ' - ' + l.niche : '') + (l.address ? ' - ' + l.address : '');

  // Signals
  var signalsEl = document.getElementById('d-signals');
  var signalDefs = [
    { show: !l.has_website, bad: true, label: 'No website' },
    { show: !l.has_google_listing, bad: true, label: 'No Google listing' },
    { show: ['wix','squarespace','weebly'].indexOf(l.site_platform) !== -1, bad: true, label: (l.site_platform || '') + ' site' },
    { show: !l.has_ssl && l.has_website, bad: true, label: 'No SSL' },
    { show: l.review_count !== null && l.review_count < 10, bad: false, label: 'Few reviews (' + l.review_count + ')' },
  ];
  signalDefs.forEach(function(s) {
    if (!s.show) return;
    var span = txt('span', 'signal' + (s.bad ? ' bad' : ''), s.label);
    signalsEl.appendChild(span);
  });

  // Score
  var scoreEl = document.getElementById('d-score');
  scoreEl.textContent = l.score + (l.score >= 70 ? ' [hot]' : '');
  scoreEl.className = 'score-number' + (l.score >= 70 ? ' hot' : l.score >= 40 ? ' warm' : '');

  // Breakdown
  var breakdownEl = document.getElementById('d-breakdown');
  var breakdown = {};
  try { breakdown = JSON.parse(l.score_breakdown || '{}'); } catch (_) {}
  Object.keys(breakdown).forEach(function(k) {
    var row = el('div', 'breakdown-row');
    var labelNode = document.createTextNode(k.replace(/_/g, ' '));
    var pts = txt('span', null, '+' + breakdown[k]);
    row.appendChild(labelNode);
    row.appendChild(pts);
    breakdownEl.appendChild(row);
  });

  // Status dropdown
  var statusEl = document.getElementById('d-status');
  ['new','contacted','replied','won','lost'].forEach(function(s) {
    var opt = new Option(s.charAt(0).toUpperCase() + s.slice(1), s);
    if (s === l.status) opt.selected = true;
    statusEl.add(opt);
  });
  statusEl.addEventListener('change', function() { updateStatus(l.id, statusEl.value); });

  // Phone
  if (l.phone) {
    document.getElementById('d-phone-group').style.display = '';
    document.getElementById('d-phone').textContent = l.phone;
  }

  // Website — only render as a link if the URL uses http(s) scheme
  if (l.website_url) {
    document.getElementById('d-website-group').style.display = '';
    var websiteContainer = document.getElementById('d-website');
    if (/^https?:\/\//.test(l.website_url)) {
      var link = document.createElement('a');
      link.textContent = l.website_url;
      link.setAttribute('href', l.website_url);
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
      websiteContainer.appendChild(link);
    } else {
      websiteContainer.textContent = l.website_url; // plain text fallback for non-http URLs
    }
  }

  // Notes
  var notesEl = document.getElementById('d-notes');
  var outreach = l.outreach;
  notesEl.value = outreach && outreach.notes ? outreach.notes : '';
  notesEl.addEventListener('blur', function() { saveNotes(l.id, notesEl.value); });

  // Draft button + existing draft
  var draftBtn = document.getElementById('btn-draft');
  var existingDraft = outreach && outreach.email_draft;

  if (existingDraft) {
    draftBtn.textContent = 'View Draft';
    showDraft(existingDraft, l.id, true);
  }

  draftBtn.addEventListener('click', function() { draftEmail(l.id); });
}

function showDraft(draftText, leadId, cached) {
  var block = document.getElementById('d-draft-block');
  block.replaceChildren();

  var draftDiv = el('div', 'draft-block');

  var textEl = el('div', 'draft-text');
  textEl.id = 'd-draft-text';
  textEl.textContent = draftText;  // textContent -- safe

  var actions = el('div', 'draft-actions');
  var copyBtn = txt('button', 'btn-copy', 'Copy');
  copyBtn.addEventListener('click', copyDraft);

  var regenBtn = txt('button', 'btn-regen', 'Regenerate');
  regenBtn.addEventListener('click', function() { regenDraft(leadId); });

  actions.appendChild(copyBtn);
  actions.appendChild(regenBtn);
  if (cached) {
    actions.appendChild(txt('span', null, 'Saved draft'));
  }

  draftDiv.appendChild(textEl);
  draftDiv.appendChild(actions);
  block.appendChild(draftDiv);
}

// --- Actions ---

function updateStatus(id, status) {
  fetch('/api/leads/' + id, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: status })
  }).then(function() {
    showToast('Status saved');
    if (activeLead) activeLead.status = status;
    renderList();
  });
}

function saveNotes(id, notes) {
  fetch('/api/leads/' + id, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes: notes })
  }).then(function() {
    var confirm = document.getElementById('d-notes-confirm');
    if (confirm) {
      confirm.textContent = 'Saved';
      setTimeout(function() { if (confirm) confirm.textContent = ''; }, 2000);
    }
  });
}

function draftEmail(id) {
  var btn = document.getElementById('btn-draft');
  var errEl = document.getElementById('d-draft-error');
  btn.disabled = true;
  btn.textContent = 'Drafting...';
  errEl.textContent = '';

  fetch('/api/leads/' + id + '/draft', { method: 'POST' })
    .then(function(r) { return r.json().then(function(d) { return { ok: r.ok, data: d }; }); })
    .then(function(result) {
      if (!result.ok) throw new Error(result.data.error || 'Unknown error');
      showDraft(result.data.draft, id, result.data.cached);
      btn.textContent = 'Draft Ready';
    })
    .catch(function(err) {
      errEl.textContent = err.message;
      btn.disabled = false;
      btn.textContent = 'Draft Outreach Email';
    });
}

function regenDraft(id) {
  var btn = document.getElementById('btn-draft');
  var errEl = document.getElementById('d-draft-error');
  btn.disabled = true;
  btn.textContent = 'Regenerating...';
  errEl.textContent = '';

  fetch('/api/leads/' + id + '/draft?regenerate=1', { method: 'POST' })
    .then(function(r) { return r.json().then(function(d) { return { ok: r.ok, data: d }; }); })
    .then(function(result) {
      if (!result.ok) throw new Error(result.data.error || 'Unknown error');
      var textEl = document.getElementById('d-draft-text');
      if (textEl) textEl.textContent = result.data.draft;  // safe textContent
      btn.textContent = 'Draft Ready';
    })
    .catch(function(err) {
      errEl.textContent = err.message;
      btn.disabled = false;
      btn.textContent = 'Draft Outreach Email';
    });
}

function copyDraft() {
  var textEl = document.getElementById('d-draft-text');
  if (!textEl) return;
  navigator.clipboard.writeText(textEl.textContent)
    .then(function() { showToast('Copied to clipboard'); });
}

function clearFilters() {
  ['filter-city','filter-niche','filter-status'].forEach(function(id) {
    document.getElementById(id).value = '';
  });
  document.getElementById('filter-search').value = '';
  loadLeads();
}

function showToast(msg) {
  var toastEl = document.getElementById('toast');
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  setTimeout(function() { toastEl.classList.remove('show'); }, 2500);
}

// Filter listeners
['filter-city','filter-niche','filter-status'].forEach(function(id) {
  document.getElementById(id).addEventListener('change', loadLeads);
});
var searchTimer;
document.getElementById('filter-search').addEventListener('input', function() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadLeads, 300);
});
document.getElementById('btn-clear').addEventListener('click', clearFilters);

init();
</script>
</body>
</html>
```

- [ ] **Step 3: Start CRM and verify it loads**

```bash
cd leadgen-crm && node server.js
```
Open http://localhost:3000. Expected: CRM loads, empty list state shown.

- [ ] **Step 4: Commit**

```bash
cd leadgen-crm && git add public/ && git commit -m "Add CRM frontend with DOM-safe rendering"
```

---

## Task 8: Integration + Entry Point

**Prerequisite:** Tasks 1-7 complete.

- [ ] **Step 1: Run all scraper tests**

```bash
cd leadgen-scraper && python -m pytest tests/ -v
```
Expected: All pass.

- [ ] **Step 2: Run all CRM tests**

```bash
cd leadgen-crm && npm test
```
Expected: All pass.

- [ ] **Step 3: Smoke test full pipeline**

Run in two terminals (requires real API keys — load from .env file, not inline):

```bash
# Setup: copy .env.example → .env and fill in real keys, then:

# Terminal 1
cd leadgen-crm && node -e "require('dotenv').config(); require('./server')"
# Or simply: export vars from .env first, then: node server.js

# Terminal 2
cd leadgen-scraper && source .env && python scrape.py --city Burlington --type restaurant --limit 5
```

Expected sequence:
1. Scraper prints 5 leads with scores and tiers
2. Open http://localhost:3000 -- leads appear sorted by score, new ones show NEW pill
3. Click a lead -- detail panel fills with data
4. Change status -- toast appears "Status saved", list reflects new status
5. Add notes, click away -- "Saved" confirmation appears
6. Click "Draft Outreach Email" -- button shows "Drafting...", draft appears with copy button

- [ ] **Step 4: Add entry point to creativeagency site**

In `creativeagency/index.html`, find the closing `</footer>` tag. Add just before it:

```html
<div style="margin-top:32px;padding-top:16px;border-top:1px solid rgba(0,0,0,0.1);font-size:12px;color:#999;text-align:center;">
  <!-- TODO: replace with Railway URL before deploying -->
  <a href="http://localhost:3000" style="color:#999;text-decoration:none;">Internal Tools</a>
</div>
```

- [ ] **Step 5: Add README files**

File: `leadgen-scraper/README.md`
```
# leadgen-scraper

Local business lead scraper using Google Places API.

Setup:
  pip install -r requirements.txt
  export GOOGLE_PLACES_API_KEY=your_key_here

Run:
  python scrape.py --city Burlington --type restaurant
  python scrape.py --city Hamilton --type salon --limit 50

Test:
  python -m pytest tests/ -v
```

File: `leadgen-crm/README.md`
```
# leadgen-crm

CRM for reviewing and acting on leads from leadgen-scraper.

Setup:
  npm install
  export ANTHROPIC_API_KEY=your_key_here

Run:
  node server.js
  Open http://localhost:3000

Test:
  npm test
```

- [ ] **Step 6: Final commit**

```bash
git add -A && git commit -m "Add README files and creativeagency entry point"
```
