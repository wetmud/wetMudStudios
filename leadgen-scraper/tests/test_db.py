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
