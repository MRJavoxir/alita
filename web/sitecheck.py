# ~/alita/web/sitecheck.py

import requests
import socket

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
def check_site(url):
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    domain = url.split("//")[1].split("/")[0]

    try:
        ip = socket.gethostbyname(domain)
    except socket.gaierror:
        print(f"{domain} — DNS lookup failed. The domain doesn't resolve (doesn't exist, or DNS is down).")
        return

    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            print(f"{domain} ({ip}) — UP. Responded normally (200 OK).")
        else:
            print(f"{domain} ({ip}) — responded, but with an error: HTTP {response.status_code} ({response.reason})")
    except requests.exceptions.ConnectTimeout:
        print(f"{domain} ({ip}) — Connection timed out. Server isn't responding (could be down, or blocking connections).")
    except requests.exceptions.ConnectionError:
        print(f"{domain} ({ip}) — Connection refused. The server actively rejected the connection.")
    except requests.exceptions.RequestException as e:
        print(f"{domain} ({ip}) — Request failed: {e}")

if __name__ == "__main__":
    url = input("Site to check: ")
    check_site(url)