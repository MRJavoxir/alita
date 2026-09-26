# ~/alita/web/whois_lookup.py

import whois

def clean_date(date_value):
    if isinstance(date_value, list):
        date_value = date_value[0]
    if date_value:
        return date_value.strftime("%Y-%m-%d")
    return "Unknown"

def clean_status(status_list):
    if not status_list:
        return []
    seen = set()
    cleaned = []
    for s in status_list:
        # strip the URL part, keep just the status name
        name = s.split(" ")[0].split("(")[0].strip()
        if name not in seen:
            seen.add(name)
            cleaned.append(name)
    return cleaned

def lookup(domain):
    try:
        data = whois.whois(domain)
    except Exception as e:
        print(f"Lookup failed: {e}")
        return

    print(f"Domain: {data.domain_name if not isinstance(data.domain_name, list) else data.domain_name[0]}")
    print(f"Registrar: {data.registrar}")
    print(f"Created: {clean_date(data.creation_date)}")
    print(f"Expires: {clean_date(data.expiration_date)}")
    print(f"Updated: {clean_date(data.updated_date)}")

    print(f"Name servers:")
    if data.name_servers:
        for ns in sorted(set(data.name_servers)):
            print(f"  {ns}")

    print(f"Status: {', '.join(clean_status(data.status))}")

    if data.emails:
        emails = data.emails if isinstance(data.emails, list) else [data.emails]
        print(f"Contact emails: {', '.join(emails)}")
    else:
        print("Contact emails: none public (privacy-protected)")

if __name__ == "__main__":
    domain = input("Domain to look up: ")
    lookup(domain)