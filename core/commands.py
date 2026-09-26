# ~/alita/core/commands.py

import subprocess
import datetime
from security import check_secret, is_stopped
from say import say
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web"))
import sitecheck, subdomains, whois_lookup, portscan, headers_check
import webbrowser
# ---- Every real app/target Alita knows about ----
APPS = {
    "browser":  {"synonyms": ["browser", "firefox", "web"],        "open_cmd": ["firefox"],                              "proc": "firefox"},
    "chromium": {"synonyms": ["chromium", "chrome"],                "open_cmd": ["chromium"],                             "proc": "chromium"},
    "brave":    {"synonyms": ["brave"],                              "open_cmd": ["brave-browser"],                        "proc": "brave"},
    "telegram": {"synonyms": ["telegram", "tg", "tj", "pg", "allegrum", "telegraph"],                     "open_cmd": ["telegram-desktop"],                     "proc": "telegram-desktop"},
    "discord":  {"synonyms": ["discord"],                            "open_cmd": ["discord"],                              "proc": "discord"},
    "hud":      {"synonyms": ["hud", "ui", "interface", "dashboard", "hot", "hood", "hub"],"open_cmd": [sys.executable, "interface/hud.py"], "proc": "interface/hud.py"},
    "claude":   {"synonyms": ["claude"],                             "open_cmd": ["firefox", "https://claude.ai"],         "proc": None},
    "youtube":  {"synonyms": ["youtube", "yt"],                      "open_cmd": ["firefox", "https://youtube.com"],       "proc": None},
    "log":      {"synonyms": ["log", "history", "activity"],        "open_cmd": None,                                     "proc": None},
    "time":     {"synonyms": ["time", "usage"],                     "open_cmd": None,                                     "proc": None},
    "website":  {"synonyms": ["website", "site", "url"],            "open_cmd": None,                                     "proc": None},
    "music":    {"synonyms": ["music", "song"],                     "open_cmd": None,                                     "proc": None},
    "scanner": {"synonyms": ["scanner"],                            "open_cmd": ["simple-scan"],                          "proc": "simple-scan"},
    "cs2":     {"synonyms": ["cs2"],                                 "open_cmd": ["steam", "steam://rungameid/730"],       "proc": None},
    "csgo":    {"synonyms": ["csgo", "counter","counterstrike", "global", "offensive"], "open_cmd": ["steam", "steam://rungameid/4465480"], "proc": "csgo_linux64"},
    "steam":   {"synonyms": ["steam"],                              "open_cmd": ["steam"],                                "proc": "steam"},
    "vscode":   {"synonyms": ["vscode", "code"],                     "open_cmd": ["code"],                                 "proc": "code"},
    "vlc":      {"synonyms": ["vlc"],                                "open_cmd": ["vlc"],                                  "proc": "vlc"},
    "terminal": {"synonyms": ["terminal"],                           "open_cmd": ["gnome-terminal"],                       "proc": "gnome-terminal"},
    "files":    {"synonyms": ["files", "nautilus"],                  "open_cmd": ["nautilus"],                             "proc": "nautilus"},
    "history":         {"synonyms": ["history"],                     "open_cmd": None, "proc": None},
    "firefoxhistory":  {"synonyms": ["firefoxhistory"],               "open_cmd": None, "proc": None},
    "chromehistory":   {"synonyms": ["chromehistory"],                "open_cmd": None, "proc": None},
    "playtime":        {"synonyms": ["playtime", "steamtime"],        "open_cmd": None, "proc": None},
    "steamhistory":    {"synonyms": ["steamhistory"],                    "open_cmd": None, "proc": None},
    "sitecheck":  {"synonyms": ["sitecheck", "site"], "open_cmd": None, "proc": None},
    "subdomains": {"synonyms": ["subdomains"], "open_cmd": None, "proc": None},
    "whois":      {"synonyms": ["whois"],      "open_cmd": None, "proc": None},
    "portscan":   {"synonyms": ["portscan", "scan"], "open_cmd": None, "proc": None},
    "headers":    {"synonyms": ["headers"],    "open_cmd": None, "proc": None},
}   

ACTIONS = {
    "open": "open", "launch": "open", "start": "open", "play": "open", "switch": "open",
    "close": "close", "quit": "close", "exit": "close", "stop": "close", "off": "close",
    "show": "show", "display": "show", "check": "show",
}

JUNK_WORDS = {
    "please", "could", "can", "you", "buddy", "man", "hey", "the",
    "my", "a", "an", "and", "to", "for", "me", "it", "on", "up",
    "whats", "what's", "yo", "now",
}

# Build a lookup: any synonym word -> the real target name
WORD_TO_TARGET = {}
for target_name, info in APPS.items():
    for word in info["synonyms"]:
        WORD_TO_TARGET[word] = target_name

LOG_PATH = os.path.expanduser("~/alita/data/activity.log")  # adjust if yours is different

def do_action(action, target, extra_text=""):
    info = APPS[target]

    if action == "show" and target == "log":
        subprocess.run(["cat", LOG_PATH])

    elif action == "show" and target == "history":
        print("--- Firefox ---")
        subprocess.run(["python3", "core/history_firefox.py"])
        print("--- Chrome/Chromium ---")
        subprocess.run(["python3", "core/history_chrome.py"])
        print("--- Steam ---")
        subprocess.run(["python3", "core/history_steam.py"])

    elif action == "show" and target == "firefoxhistory":
        subprocess.run(["python3", "core/history_firefox.py"])

    elif action == "show" and target == "chromehistory":
        subprocess.run(["python3", "core/history_chrome.py"])

    elif action == "show" and target in ("playtime", "steamhistory"):
        subprocess.run(["python3", "core/history_steam.py"])

    elif action == "open" and target == "website":
        url = extra_text.strip()
        if not url:
            say("Which website?")
            return
        if not url.startswith("http"):
            url = "https://" + url
        site_name = extra_text.strip().replace("https://", "").replace("http://", "").replace("www.", "").split(".")[0]
        say(f"Opening {site_name}.")
        subprocess.Popen(["gio", "launch", "/usr/share/applications/firefox.desktop", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    elif action == "open" and target == "music":
        song = extra_text.strip()
        if not song:
            say("Which song?")
            return
        say(f"Playing {song}.")
        subprocess.Popen(
            f'python3 -m yt_dlp -f bestaudio -o - "ytsearch1:{song}" | mpv --no-video -',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )

    elif action == "close" and target == "music":
        say("Stopping music.")
        subprocess.run(["pkill", "-f", "mpv"])

    elif action == "open":
        if info["open_cmd"]:
            say(f"Opening {target}.")
            subprocess.Popen(info["open_cmd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        else:
            print(f"I don't have an 'open' action for {target} yet.")

    elif action == "close":
        if info["proc"]:
            t = say(f"Closing {target}.")
            if t is not None:
                t.join()
            subprocess.run(["pkill", "-f", info["proc"]])
        else:
            print(f"I don't have a 'close' action for {target} yet.")
    
    elif action == "show" and target == "time":
        app_name = extra_text.strip().lower()
        if not app_name:
            say("Which app?")
            return
        import sys, os as _os
        sys.path.append(_os.path.dirname(_os.path.abspath(__file__)))
        from time_summary import calculate_time_per_title
        log_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "activity.log")
        totals = calculate_time_per_title(log_path)
        matched = datetime.timedelta()
        for title, duration in totals.items():
            if app_name in title.lower():
                matched += duration
        hours = matched.total_seconds() / 3600
        msg = f"You've used {app_name} for about {hours:.1f} hours."
        print(msg)
        say(msg)

    elif action == "show" and target == "sitecheck":
        url = extra_text.strip()
        if not url:
            say("Which site?")
            return
        sitecheck.check_site(url)

    elif action == "show" and target == "subdomains":
        domain = extra_text.strip()
        if not domain:
            say("Which domain?")
            return
        subdomains.find_subdomains(domain)

    elif action == "show" and target == "whois":
        domain = extra_text.strip()
        if not domain:
            say("Which domain?")
            return
        whois_lookup.lookup(domain)

    elif action == "show" and target == "portscan":
        target_host = extra_text.strip()
        if not target_host:
            say("Which target?")
            return
        portscan.scan(target_host)

    elif action == "show" and target == "headers":
        url = extra_text.strip()
        if not url:
            say("Which site?")
            return
        headers_check.check_headers(url)

    else:
        print(f"I know '{action}' and '{target}', but not that combo yet.")
def run_command(sentence, quiet=False):
    if check_secret(sentence):
        return True

    if is_stopped():
        print("Alita is paused. Say 'alita lights up' to resume.")
        return True

    words = [w.strip(",.!?") for w in sentence.lower().split()]
    words = [w for w in words if w not in JUNK_WORDS]

    # merge two-word phrases like "firefox history" into one known target word,
    # before anything else runs
    PHRASES = {
        ("firefox", "history"): "firefoxhistory",
        ("chrome", "history"): "chromehistory",
        ("chromium", "history"): "chromehistory",
        ("steam", "history"): "steamhistory",
    }
    merged_words = []
    i = 0
    while i < len(words):
        if i + 1 < len(words) and (words[i], words[i + 1]) in PHRASES:
            merged_words.append(PHRASES[(words[i], words[i + 1])])
            i += 2
        else:
            merged_words.append(words[i])
            i += 1
    words = merged_words

    # split glued words like "opentg" into "open tg" (only if the rest is a known menu word,
    # and the whole word isn't ALREADY a valid target on its own, like "playtime")
    split_words = []
    for w in words:
        if w in WORD_TO_TARGET:
            split_words.append(w)
            continue
        for act in ACTIONS:
            if w.startswith(act) and len(w) > len(act) and w[len(act):] in WORD_TO_TARGET:
                split_words += [act, w[len(act):]]
                break
        else:
            split_words.append(w)
    words = split_words

    current_action = None
    found_anything = False

    for i, word in enumerate(words):
        if word in ACTIONS:
            current_action = ACTIONS[word]
        elif word in WORD_TO_TARGET:
            target = WORD_TO_TARGET[word]
            if current_action:
                extra_text = " ".join(words[i + 1:])
                do_action(current_action, target, extra_text)
                found_anything = True
                break

    if not found_anything:
        if not quiet:
            print("unknown command")
            say("Sorry, that one is not on my menu.")
        return False
    return True

if __name__ == "__main__":
    while True:
        text = input("alita> ")
        if text.lower() == "exit":
            break
        run_command(text)