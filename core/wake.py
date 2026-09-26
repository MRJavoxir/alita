import subprocess
import time
import fcntl
import sys
import os
import atexit
import signal
import threading

NORMAL_MIC_SOURCE = "alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp_6__source"

def _handle_exit_signal(signum, frame):
    sys.exit(0)

subprocess.run(["pactl", "set-default-source", NORMAL_MIC_SOURCE])
subprocess.run(["pactl", "set-source-volume", NORMAL_MIC_SOURCE, "300%"])
print("Using normal mic, gain boosted.", flush=True)
signal.signal(signal.SIGINT, _handle_exit_signal)
signal.signal(signal.SIGTERM, _handle_exit_signal)

# single-instance guard: the OS releases this lock automatically if Alita dies, so it can never get stuck
_lock_file = open("/tmp/alita_wake.lock", "w")
try:
    fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError:
    print("Alita is already running.", flush=True)
    sys.exit(1)

import numpy as np
from openwakeword.model import Model
from say import say
from stt import listen_and_transcribe, _get_model
from commands import run_command
import hud_bridge
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brain"))
from ai import ask_ai
from chat_mode import run_chat_mode, is_alita_command, strip_to_command, is_chat_mode_phrase

THRESHOLD = 0.35
CHUNK = 1280

print("loading wake word model...", flush=True)
model = Model(
    wakeword_models=[os.path.expanduser("~/alita/core/hey_alita.onnx")],
    inference_framework="onnx",
    vad_threshold=0.5,
)
print("model loaded, ready", flush=True)
print("loading speech model...", flush=True)
_get_model()
print("speech model ready", flush=True)
hud_bridge.set_state("idle")


def wait_for_wake():
    for _ in range(40):
        model.predict(np.zeros(CHUNK, dtype=np.int16))
    print("starting mic stream...", flush=True)
    mic = subprocess.Popen(
        ["timeout", "30", "arecord", "-q", "-D", "pulse", "-f", "S16_LE", "-r", "16000", "-c", "1", "-t", "raw"],
        stdout=subprocess.PIPE,
    )
    print("mic stream started, listening...", flush=True)
    try:
        while True:
            data = mic.stdout.read(CHUNK * 2)
            if len(data) < CHUNK * 2:
                raise RuntimeError("mic stream ended or timed out")
            audio = np.frombuffer(data, dtype=np.int16)
            score = model.predict(audio)["hey_alita"]
            if score >= THRESHOLD:
                return score
    finally:
        mic.terminate()
        mic.wait()


_typed_pending_command = [False]

def _run_typed_command(text):
    try:
        matched = run_command(text, quiet=True)
        if not matched:
            ai_guess = ask_ai(text)
            if ai_guess:
                print(f"[ai] matched to: {ai_guess}", flush=True)
                run_command(f"{ai_guess} {text}")
            else:
                print("unknown command", flush=True)
                say("Sorry, that one is not on my menu.")
    except Exception as e:
        print(f"command crashed: {e}", flush=True)
        say("Sorry, something went wrong with that.")

def handle_typed_command(text):
    print(f"[typed] {text}", flush=True)
    hud_bridge.add_message("user", text)

    if _typed_pending_command[0]:
        _typed_pending_command[0] = False
        print("[typed] -> COMMAND (pending)", flush=True)
        _run_typed_command(text)
        return

    if is_alita_command(text):
        remainder = strip_to_command(text)
        if not remainder:
            t = say("Yes?")
            if t is not None:
                t.join()
            _typed_pending_command[0] = True
            return
        text = remainder

    if is_chat_mode_phrase(text):
        t = say("I'm listening.")
        if t is not None:
            t.join()
        run_chat_mode(_get_model())
        return

    _run_typed_command(text)

def typed_input_loop():
    while True:
        text = hud_bridge.pop_typed_input()
        if text:
            handle_typed_command(text)
        time.sleep(0.3)

if __name__ == "__main__":
    print("Listening for 'hey alita'. Ctrl+C to stop.", flush=True)
    threading.Thread(target=typed_input_loop, daemon=True).start()
    try:
        while True:
            hud_bridge.set_state("idle")
            try:
                score = wait_for_wake()
            except RuntimeError as e:
                print(e, flush=True)
                time.sleep(2)
                continue
            print(f"wake! score {score:.2f}", flush=True)
            t = say("Yes?")
            if t is not None:
                t.join()
            time.sleep(0.2)
            print("recording command...", flush=True)
            heard = listen_and_transcribe()
            print(f"heard: {heard}", flush=True)
            if heard:
                hud_bridge.add_message("user", heard)

            _filler = {"alita", "hey", "ok", "okay", ""}
            _stripped = [w.strip(",.!?").lower() for w in heard.split()]
            _meaningful = [w for w in _stripped if w not in _filler]
            if len(_meaningful) < 2:
                print("heard only wake-word/noise, ignoring", flush=True)
                time.sleep(1.0)
                continue

            if is_chat_mode_phrase(heard):
                t = say("I'm listening.")
                if t is not None:
                    t.join()
                run_chat_mode(_get_model())
                time.sleep(1.0)
                continue

            try:
                matched = run_command(heard, quiet=True)
                if not matched:
                    ai_guess = ask_ai(heard)
                    if ai_guess:
                        print(f"[ai] matched to: {ai_guess}", flush=True)
                        run_command(f"{ai_guess} {heard}")
                    else:
                        print("unknown command", flush=True)
                        say("Sorry, that one is not on my menu.")
            except Exception as e:
                print(f"command crashed: {e}", flush=True)
                say("Sorry, something went wrong with that.")
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
