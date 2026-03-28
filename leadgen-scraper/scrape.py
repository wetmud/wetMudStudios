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
