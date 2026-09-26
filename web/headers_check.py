# ~/alita/web/headers_check.py

import requests

HEADERS_REQ = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Current (2026) recommended security headers, with what each one protects against
SECURITY_HEADERS = {
    "strict-transport-security": "Forces HTTPS, prevents SSL-stripping attacks",
    "content-security-policy": "Blocks XSS by restricting where scripts/content can load from",
    "x-content-type-options": "Stops browsers from guessing file types (MIME sniffing attacks)",
    "x-frame-options": "Prevents clickjacking (page being loaded in a hidden iframe)",
    "referrer-policy": "Controls how much URL info leaks when clicking links away from the site",
    "permissions-policy": "Restricts access to camera, mic, location, etc.",
}

# Headers that leak useful recon info about the server
INFO_LEAK_HEADERS = ["server", "x-powered-by", "x-aspnet-version"]

def check_headers(url):
    if not url.startswith("http"):
        url = "https://" + url

    try:
        response = requests.get(url, headers=HEADERS_REQ, timeout=5)
    except requests.exceptions.RequestException as e:
        print(f"Couldn't connect: {e}")
        return

    resp_headers = {k.lower(): v for k, v in response.headers.items()}

    print(f"Status: HTTP {response.status_code}\n")

    print("--- Security headers ---")
    for header, purpose in SECURITY_HEADERS.items():
        if header in resp_headers:
            value = resp_headers[header]
            if len(value) > 100:
                value = value[:100] + f"... ({len(value)} chars total, truncated)"
            print(f"  ✓ {header}: {value}")
        else:
            print(f"  ✗ MISSING: {header} — {purpose}")

    print("\n--- Info leaks ---")
    leaked = False
    for header in INFO_LEAK_HEADERS:
        if header in resp_headers:
            print(f"  {header}: {resp_headers[header]}  (reveals server software/version)")
            leaked = True
        if not leaked:
            print("  None found — server isn't revealing software/version info.")

if __name__ == "__main__":
    url = input("Site to check: ")
    check_headers(url)