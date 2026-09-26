# ~/alita/core/history_firefox.py

import sqlite3
import shutil
import os
import glob

def find_places_db():
    patterns = [
        "~/.config/mozilla/firefox/*.default-release/places.sqlite",
        "~/.mozilla/firefox/*.default-release/places.sqlite",
        "~/snap/firefox/common/.mozilla/firefox/*.default*/places.sqlite",
    ]
    for pattern in patterns:
        matches = glob.glob(os.path.expanduser(pattern))
        if matches:
            return matches[0]
    return None

DB_PATH = find_places_db()
TEMP_COPY = "/tmp/firefox_history_copy.sqlite"

def clean_url(url):
    # Strip off everything after ? (tracking junk) for a cleaner look
    return url.split("?")[0]

def get_firefox_history(limit=15):
    if not DB_PATH:
        print("Could not find Firefox's history database.")
        return
    shutil.copy2(DB_PATH, TEMP_COPY)

    conn = sqlite3.connect(TEMP_COPY)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT url, title
        FROM moz_places
        WHERE last_visit_date IS NOT NULL
        AND title IS NOT NULL
        ORDER BY last_visit_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    seen = set()
    count = 0
    for url, title in rows:
        clean = clean_url(url)
        if clean in seen:
            continue  # skip duplicates, only show each site once
        seen.add(clean)
        print(f"{title} — {clean}")
        count += 1
        if count >= limit:
            break

if __name__ == "__main__":
    get_firefox_history()