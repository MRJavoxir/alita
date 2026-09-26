# ~/alita/web/subdomains.py

import requests

def find_subdomains(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"Couldn't fetch data: {e}")
        return

    found = set()
    for entry in data:
        name = entry.get("name_value", "")
        for line in name.split("\n"):
            line = line.strip().lower()
            if line.endswith(domain):
                found.add(line)

    if not found:
        print(f"No subdomains found for {domain}.")
        return

    print(f"Found {len(found)} subdomains for {domain}:")
    for sub in sorted(found):
        print(f"  {sub}")

if __name__ == "__main__":
    domain = input("Domain (e.g. example.com): ")
    find_subdomains(domain)