# ~/alita/web/portscan.py

import socket

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 8080: "HTTP-Alt",
}

def scan(target, ports=None):
    if ports is None:
        ports = COMMON_PORTS.keys()

    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        print(f"Couldn't resolve {target}")
        return

    print(f"Scanning {target} ({ip})...\n")

    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        service = COMMON_PORTS.get(port, "Unknown")
        if result == 0:
            print(f"  {port}/tcp  OPEN    ({service})")
        sock.close()

    print("\nDone. (Ports not listed above were closed or filtered.)")

if __name__ == "__main__":
    target = input("Target (domain or IP): ")
    scan(target)