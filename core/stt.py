import subprocess, wave
import numpy as np
from faster_whisper import WhisperModel

MODEL_NAME = "base.en"
TMP_WAV = "/tmp/alita_command.wav"
RATE = 16000
CHUNK = 1600         # 100ms
SILENCE_LIMIT = 10   # ~1.8s pause allowed before cutting off, was 1.2s
MAX_CHUNKS = 60      # 6s hard cap
SILENCE_AMP = 400    # below this = silence

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8", cpu_threads=4)
    return _model

def _record_until_silence():
    proc = subprocess.Popen(
        ["arecord", "-q", "-D", "pulse", "-f", "S16_LE", "-r", str(RATE), "-c", "1", "-t", "raw"],
        stdout=subprocess.PIPE,
    )
    chunks, silent_run, heard_speech = [], 0, False
    try:
        for _ in range(MAX_CHUNKS):
            data = proc.stdout.read(CHUNK * 2)
            if len(data) < CHUNK * 2:
                break
            chunks.append(data)
            amp = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
            if amp > SILENCE_AMP:
                heard_speech, silent_run = True, 0
            elif heard_speech:
                silent_run += 1
                if silent_run >= SILENCE_LIMIT:
                    break
    finally:
        proc.terminate()
        proc.wait()
    return b"".join(chunks)

def listen_and_transcribe():
    import time as _t
    _t0 = _t.time()
    raw = _record_until_silence()
    _t1 = _t.time()
    with wave.open(TMP_WAV, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(raw)
    model = _get_model()
    segments, _ = model.transcribe(TMP_WAV, language="en", beam_size=5, vad_filter=True,
                                    hotwords="Alita open close show lock scrub empty dark lights Discord Firefox Steam VLC Telegram YouTube Chromium Counter Strike CSGO VS Code chat mode")
    text = " ".join(s.text.strip() for s in segments)
    print(f"[timing] record {_t1-_t0:.1f}s | transcribe {_t.time()-_t1:.1f}s", flush=True)
    return text
