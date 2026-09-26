# ~/alita/core/history_chrome.py

import sqlite3
import shutil
import os

DB_PATH = os.path.expanduser(
    "~/snap/chromium/common/chromium/Default/History"
)
TEMP_COPY = "/tmp/chromium_history_copy.sqlite"

def clean_url(url):
    return url.split("?")[0]

def get_chrome_history(limit=15):
    shutil.copy2(DB_PATH, TEMP_COPY)

    conn = sqlite3.connect(TEMP_COPY)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT url, title
        FROM urls
        WHERE title IS NOT NULL AND title != ''
        ORDER BY last_visit_time DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    seen = set()
    count = 0
    for url, title in rows:
        clean = clean_url(url)
        if clean in seen:
            continue
        seen.add(clean)
        print(f"{title} — {clean}")
        count += 1
        if count >= limit:
            break

if __name__ == "__main__":
    get_chrome_history()