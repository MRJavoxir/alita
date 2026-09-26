import json, os, time

STATUS_FILE = os.path.expanduser("~/alita/data/hud_status.json")

def _read():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"state": "listening", "messages": []}

def _write(data):
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    tmp = STATUS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, STATUS_FILE)

def set_state(state):
    data = _read()
    data["state"] = state
    _write(data)

def add_message(role, text):
    data = _read()
    msgs = data.get("messages", [])
    msgs.append({"role": role, "text": text, "ts": time.time()})
    data["messages"] = msgs[-30:]
    _write(data)

def set_typed_input(text):
    data = _read()
    data["typed_input"] = text
    _write(data)

def pop_typed_input():
    data = _read()
    text = data.get("typed_input")
    if text:
        data["typed_input"] = None
        _write(data)
    return text
