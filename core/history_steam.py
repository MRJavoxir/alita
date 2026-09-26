# ~/alita/core/history_steam.py

import vdf
import os
import glob

STEAMAPPS_PATH = os.path.expanduser("~/.local/share/Steam/steamapps")
LOCALCONFIG_PATH = os.path.expanduser(
    "~/.local/share/Steam/userdata"
)

# Manual fallback for games with no local manifest
MANUAL_NAMES = {
    "730": "Counter-Strike 2",
    "4465480": "Counter-Strike: Global Offensive",
}

def get_game_name(app_id):
    if app_id in MANUAL_NAMES:
        return MANUAL_NAMES[app_id]
    manifest_path = os.path.join(STEAMAPPS_PATH, f"appmanifest_{app_id}.acf")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            data = vdf.load(f)
            return data.get("AppState", {}).get("name", f"Unknown ({app_id})")
    return f"Unknown ({app_id})"

def minutes_to_readable(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def get_steam_playtime():
    # Find the localconfig.vdf file (inside a numbered user folder)
    config_files = glob.glob(
        os.path.join(LOCALCONFIG_PATH, "*", "config", "localconfig.vdf")
    )
    if not config_files:
        print("Couldn't find localconfig.vdf — check your Steam userdata path.")
        return

    with open(config_files[0], "r") as f:
        data = vdf.load(f)

    apps = data.get("UserLocalConfigStore", {}).get("Software", {}).get("Valve", {}).get("Steam", {}).get("apps", {})

    for app_id, info in apps.items():
        playtime = info.get("Playtime", 0)
        if playtime and int(playtime) > 0:
            name = get_game_name(app_id)
            print(f"{name} — {minutes_to_readable(int(playtime))}")

if __name__ == "__main__":
    get_steam_playtime()