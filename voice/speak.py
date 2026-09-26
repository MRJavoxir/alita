import os
import re
import queue
import tempfile
import threading
import subprocess
from pathlib import Path

from kokoro_onnx import Kokoro
import soundfile as sf

MODEL_PATH = Path.home() / "alita" / "voice" / "audition" / "kokoro-v1.0.onnx"
VOICES_PATH = Path.home() / "alita" / "voice" / "audition" / "voices-v1.0.bin"
VOICE = "af_heart"

# Loaded once when this file is imported, not every time speak() is called.
print("Loading voice...")
_kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
print("Voice ready.")


def _split_sentences(text):
    # Splits on . ! ? while keeping the punctuation attached to each sentence.
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]


def speak(text):
    sentences = _split_sentences(text)
    if not sentences:
        return

    audio_queue = queue.Queue()

    def generate_worker():
        for sentence in sentences:
            samples, sr = _kokoro.create(sentence, voice=VOICE, speed=1.0, lang="en-us")
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(tmp.name, samples, sr)
            audio_queue.put(tmp.name)
        audio_queue.put(None)  # signals "no more sentences"

    # Generation runs in the background while we play whatever's ready.
    gen_thread = threading.Thread(target=generate_worker)
    gen_thread.start()

    while True:
        wav_path = audio_queue.get()
        if wav_path is None:
            break
        subprocess.run(["aplay", "-q", wav_path])
        os.remove(wav_path)

    gen_thread.join()


if __name__ == "__main__":
    import sys
    test_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "This is a test of the voice system."
    speak(test_text)