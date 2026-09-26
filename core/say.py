import os
import re
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.normpath(os.path.join(HERE, "..", "voice"))
CACHE_DIR = os.path.join(VOICE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

_lock = threading.Lock()
_speaking = threading.Event()

def _cache_path(text):
    name = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]
    return os.path.join(CACHE_DIR, name + ".wav")

def _render(text, path):
    sys.path.append(VOICE_DIR)
    import soundfile as sf
    import speak as _speak
    samples, sr = _speak._kokoro.create(text, voice=_speak.VOICE, speed=1.0, lang="en-us")
    sf.write(path, samples, sr)

def prepare(text):
    path = _cache_path(text)
    if not os.path.exists(path):
        _render(text, path)
    return path

import hud_bridge

def say(text):
    _speaking.set()  # set BEFORE the thread starts, closes the race with wait_until_done()
    def work():
        with _lock:
            hud_bridge.set_state("speaking")
            hud_bridge.add_message("assistant", text)
            path = prepare(text)
            subprocess.run(["aplay", "-q", path])
            hud_bridge.set_state("listening")
            _speaking.clear()
    t = threading.Thread(target=work)
    t.start()
    return t

def wait_until_done():
    import time
    time.sleep(0.05)
    while _speaking.is_set():
        time.sleep(0.05)
