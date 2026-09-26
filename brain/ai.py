# ~/alita/brain/ai.py
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core"))

import requests
from commands import APPS

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:0.6b"

def _build_menu():
    lines = []
    for target, info in APPS.items():
        if info.get("open_cmd"):
            lines.append(f"open {target}")
        if info.get("proc"):
            lines.append(f"close {target}")
    lines += ["open website", "open music", "close music"]
    lines += ["show history", "show sitecheck", "show subdomains", "show whois", "show portscan", "show headers", "show time"]
    return lines

def ask_ai(sentence):
    menu = _build_menu()
    menu_text = "\n".join(menu)
    prompt = (
        "You match a spoken sentence to the closest command from a fixed list.\n"
        "Reply with ONLY the exact matching line, nothing else. If truly nothing fits, reply: none\n\n"
        "Examples:\n"
        "List:\nopen discord\nclose discord\nopen music\nshow time\n"
        "Spoken: \"kill that discord thing\"\nAnswer: close discord\n\n"
        "List:\nopen discord\nclose discord\nopen music\nshow time\n"
        "Spoken: \"play thunderstruck by acdc\"\nAnswer: open music\n\n"
        "List:\nopen discord\nclose discord\nopen music\nshow time\n"
        "Spoken: \"how long have I used discord\"\nAnswer: show time\n\n"
        "Now the real one:\n"
        f"List:\n{menu_text}\n\n"
        f"Spoken: \"{sentence}\"\n"
        "Answer:"
    )
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False, "think": False,
            "keep_alive": "30m",
            "options": {"temperature": 0},
        }, timeout=30)
        resp.raise_for_status()
        answer = resp.json().get("response", "").strip().lower()
    except Exception as e:
        print(f"[ai] error talking to ollama: {e}", flush=True)
        return None
    return answer if answer in menu else None
