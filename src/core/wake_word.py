"""
Wake word detection using faster-whisper with a sliding window.
Checks every 0.4s on a 1.2s rolling audio buffer — ~0.4s detection delay.
Say "Hey SARA" or just "SARA" to activate.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# ── Config ────────────────────────────────────────────────────────────────────
WAKE_PHRASES  = ["sara", "hey sara", "hey, sara"]
SAMPLE_RATE   = 16000
STEP_SECONDS  = 0.4                             # how often to run inference
WINDOW_SECONDS = 1.2                            # rolling audio window to analyse
STEP_SAMPLES  = int(SAMPLE_RATE * STEP_SECONDS)
WINDOW_SAMPLES = int(SAMPLE_RATE * WINDOW_SECONDS)
SILENCE_THRESHOLD = 0.003
# ─────────────────────────────────────────────────────────────────────────────

_model = None

def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _model


def wait_for_wake_word() -> bool:
    """
    Block until "Hey SARA" is heard.
    Streams mic in 0.4s steps, analyses a 1.2s rolling window each step.
    Max detection delay: ~0.4s.
    """
    model = _get_model()
    buffer = np.zeros(WINDOW_SAMPLES, dtype=np.float32)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype="int16", blocksize=STEP_SAMPLES) as stream:
        while True:
            chunk, _ = stream.read(STEP_SAMPLES)
            step_audio = np.frombuffer(chunk.tobytes(), dtype=np.int16).astype(np.float32) / 32768.0

            # Slide the buffer forward
            buffer = np.roll(buffer, -STEP_SAMPLES)
            buffer[-STEP_SAMPLES:] = step_audio

            # Skip silent windows
            if np.abs(buffer).mean() < SILENCE_THRESHOLD:
                continue

            segments, _ = model.transcribe(
                buffer,
                language="en",
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text = " ".join(s.text for s in segments).strip().lower()

            if any(phrase in text for phrase in WAKE_PHRASES):
                print(f"[WAKE] Detected: '{text}'")
                return True


def is_active() -> bool:
    return True
