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
        time.sleep(2)
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
