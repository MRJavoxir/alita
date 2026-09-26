# ~/alita/core/chat_mode.py
import sounddevice as sd
import numpy as np
import threading
import time
import requests
import sys
import subprocess
import json
import re
import queue
import os
import soundfile as sf
from ten_vad import TenVad
import hud_bridge

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "voice"))
import speak as alita_speak

from commands import run_command
from say import wait_until_done, _lock, _speaking

HOP_SIZE = 256
THRESHOLD = 0.5
SAMPLE_RATE = 16000
SILENCE_FRAMES_TO_STOP = 63  # ~1.0s, was 80 (~1.28s)
CHAT_TIMEOUT_SECONDS = 180

vad = TenVad(HOP_SIZE, THRESHOLD)

def record_until_silence(max_wait_seconds=None):
    print("Waiting for you to start talking...", flush=True)
    recording = []
    triggered = False
    silence_count = 0
    done = threading.Event()
    start_time = time.time()
    timed_out = [False]

    def callback(indata, frames, time_info, status):
        nonlocal triggered, silence_count
        if done.is_set():
            return
        if max_wait_seconds and not triggered and (time.time() - start_time) > max_wait_seconds:
            timed_out[0] = True
            done.set()
            return
        audio = (indata[:, 0] * 32767).astype(np.int16)
        prob, is_speech = vad.process(audio)
        if is_speech:
            if not triggered:
                print("Speech started, recording...", flush=True)
            triggered = True
            silence_count = 0
            recording.append(audio.copy())
        elif triggered:
            recording.append(audio.copy())
            silence_count += 1
            if silence_count > SILENCE_FRAMES_TO_STOP:
                done.set()

    with sd.InputStream(channels=1, samplerate=SAMPLE_RATE, blocksize=HOP_SIZE, callback=callback):
        done.wait()

    if timed_out[0] or not recording:
        return None
    return np.concatenate(recording)

def transcribe(audio, whisper_model):
    segments, info = whisper_model.transcribe(
        audio.astype(np.float32) / 32768.0,
        language="en",
        hotwords="Alita, hey Alita, Discord, Telegram, Chromium, Brave, YouTube, VLC, Steam, CS2, CS:GO, Firefox, history, weather, site, subdomains, whois, portscan, headers, playtime"
    )
    return " ".join(s.text for s in segments).strip()

def extract_sentences(buffer):
    sentences = []
    while True:
        match = re.search(r'([.!?,]|--| - )(\s|$)', buffer)
        word_count = len(buffer.split())
        if not match and word_count < 10:
            break
        if match:
            end = match.end(1)
        else:
            words = buffer.split()
            cut_word = " ".join(words[:10])
            end = buffer.find(cut_word) + len(cut_word)
        chunk = buffer[:end].strip()
        if chunk:
            sentences.append(chunk)
        buffer = buffer[end:].lstrip()
    return sentences, buffer

def extract_first_chunk(buffer, min_words=4):
    """Grab a short first chunk (~min_words) as soon as there's enough text,
    so Kokoro has very little to generate before the reply starts playing.
    Only used for the very first chunk of each reply."""
    words = buffer.split()
    if len(words) < min_words:
        return None, buffer
    match = re.search(r'([.!?,]|--| - )(\s|$)', buffer)
    if match and len(buffer[:match.end(1)].split()) <= min_words:
        end = match.end(1)
    else:
        cut_word = " ".join(words[:min_words])
        end = buffer.find(cut_word) + len(cut_word)
    chunk = buffer[:end].strip()
    return chunk, buffer[end:].lstrip()

def speak_reply(user_text):
    sentence_q = queue.Queue()
    audio_q = queue.Queue()

    def ollama_stream_worker():
        buffer = ""
        full_reply_parts = []
        _t_start = time.time()
        _first_token = [None]
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "qwen3:0.6b",
            "prompt": f"You are Alita, a helpful voice assistant. Reply casually and briefly in 1-2 short sentences, plain text only, no emojis, no emoticons, no asking what else I need: {user_text}",
            "stream": True, "think": False,
            "keep_alive": "30m",
            "options": {"num_predict": 60, "temperature": 0.4}
        }, stream=True)
        first_chunk_sent = False
        printed_prefix = False
        for line in response.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            token = data.get("response", "")
            if _first_token[0] is None:
                _first_token[0] = time.time()
                print(f"[timing] ollama first token: {_first_token[0]-_t_start:.2f}s", flush=True)
            if not printed_prefix:
                print("Alita: ", end="", flush=True)
                printed_prefix = True
            print(token, end="", flush=True)
            buffer += token
            full_reply_parts.append(token)
            if not first_chunk_sent:
                chunk, buffer = extract_first_chunk(buffer)
                if chunk:
                    sentence_q.put(chunk)
                    first_chunk_sent = True
            else:
                sentences, buffer = extract_sentences(buffer)
                for s in sentences:
                    sentence_q.put(s)
            if data.get("done"):
                break
        print(flush=True)
        leftover = buffer.strip()
        if leftover:
            sentence_q.put(leftover)
        full_reply = "".join(full_reply_parts).strip()
        if full_reply:
            hud_bridge.add_message("assistant", full_reply)
        sentence_q.put(None)

    def tts_worker():
        i = 0
        while True:
            sentence = sentence_q.get()
            if sentence is None:
                audio_q.put(None)
                break
            samples, sr = alita_speak._kokoro.create(sentence, voice=alita_speak.VOICE, speed=1.0, lang="en-us")
            fname = f"/tmp/chat_chunk_{i}.wav"
            sf.write(fname, samples, sr)
            audio_q.put(fname)
            i += 1

    t1 = threading.Thread(target=ollama_stream_worker)
    t2 = threading.Thread(target=tts_worker)
    t1.start()
    t2.start()

    _speaking.set()
    hud_bridge.set_state("speaking")
    with _lock:
        _last_time = [time.time()]
        while True:
            fname = audio_q.get()
            if fname is None:
                break
            _now = time.time()
            print(f"[timing] gap before chunk: {_now-_last_time[0]:.2f}s", flush=True)
            subprocess.run(["aplay", fname])
            _last_time[0] = time.time()

        t1.join()
        t2.join()
        time.sleep(1.0)  # let room echo/device pop settle before mic reopens
    _speaking.clear()
    hud_bridge.set_state("listening")

def quick_speak(text):
    samples, sr = alita_speak._kokoro.create(text, voice=alita_speak.VOICE, speed=1.0, lang="en-us")
    sf.write("/tmp/chat_quick.wav", samples, sr)
    subprocess.run(["aplay", "/tmp/chat_quick.wav"])
    time.sleep(0.8)  # let room echo settle before mic reopens

def is_chat_mode_phrase(text):
    normalized = "".join(c for c in text.lower() if c.isalnum())
    return "chatmod" in normalized

def is_alita_command(text):
    words = [w.strip(",.!?") for w in text.lower().split()]
    first_few = words[:4]
    return "alita" in first_few

FILLER_WORDS = {"hey", "ok", "okay", "alita"}

def strip_to_command(text):
    words = text.lower().split()
    idx = None
    for i, w in enumerate(words):
        if w.strip(",.!?") == "alita":
            idx = i
            break
    if idx is None:
        return ""
    remainder = words[idx + 1:]
    while remainder and remainder[0].strip(",.!?") in FILLER_WORDS:
        remainder.pop(0)
    return " ".join(remainder).strip()

def run_chat_mode(whisper_model):
    print("=== Chat mode active ===", flush=True)
    pending_command = False
    while True:
        audio = record_until_silence(max_wait_seconds=CHAT_TIMEOUT_SECONDS)
        if audio is None:
            print("No speech for a while, leaving chat mode.", flush=True)
            return

        text = transcribe(audio, whisper_model)
        if not text:
            continue
        print(f"[chat] heard: {text}", flush=True)
        hud_bridge.add_message("user", text)

        if pending_command:
            print("[chat] -> COMMAND (pending)", flush=True)
            run_command(text)
            wait_until_done()
            pending_command = False
            continue

        if is_alita_command(text):
            remainder = strip_to_command(text)
            if not remainder:
                quick_speak("Go ahead.")
                pending_command = True
                continue
            print("[chat] -> COMMAND", flush=True)
            run_command(remainder)
            wait_until_done()
        else:
            print("[chat] -> CONVERSATION", flush=True)
            speak_reply(text)
