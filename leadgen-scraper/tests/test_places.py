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
