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
