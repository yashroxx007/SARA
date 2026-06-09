"""
Wake word detection using faster-whisper — no model training, no API key.
Listens in 1.5-second chunks, transcribes, checks for "sara" or "hey sara".

Say "Hey SARA" (or just "SARA") to activate.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# ── Config ────────────────────────────────────────────────────────────────────
WAKE_PHRASES    = ["sara", "hey sara", "hey, sara"]
SAMPLE_RATE     = 16000
CHUNK_SECONDS   = 1.5   # length of each listen window
CHUNK_SAMPLES   = int(SAMPLE_RATE * CHUNK_SECONDS)
# ─────────────────────────────────────────────────────────────────────────────

_model = None

def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        # Reuse the same tiny model — loaded once, shared with main transcription
        _model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _model


def wait_for_wake_word() -> bool:
    """
    Block until "Hey SARA" (or just "SARA") is heard.
    Streams mic in 1.5-second chunks, transcribes each with faster-whisper tiny.
    Returns True when wake phrase detected.
    """
    model = _get_model()

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype="int16", blocksize=CHUNK_SAMPLES) as stream:
        while True:
            chunk, _ = stream.read(CHUNK_SAMPLES)
            audio = np.frombuffer(chunk.tobytes(), dtype=np.int16).astype(np.float32) / 32768.0

            # Skip near-silent frames to save CPU
            if np.abs(audio).mean() < 0.002:
                continue

            segments, _ = model.transcribe(
                audio,
                language="en",
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False
            )
            text = " ".join(s.text for s in segments).strip().lower()

            if any(phrase in text for phrase in WAKE_PHRASES):
                print(f"[WAKE] Detected: '{text}'")
                return True


def is_active() -> bool:
    return True
