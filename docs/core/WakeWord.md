# Core — Wake Word

**Status:** ✅ Live — no key, no training, no account  
**File:** `src/core/wake_word.py`  
**Added:** v0.5.0 · **Updated:** v0.5.2

---

## What It Does

Always-on wake word detection using **faster-whisper** — the same model already running for STT. Listens in 1.5-second chunks, transcribes each one, activates on "SARA" or "Hey SARA".

---

## Wake Phrase

**Say "Hey SARA"** (or just **"SARA"**) to activate.

Detected phrases (case-insensitive):
- `"sara"`
- `"hey sara"`
- `"hey, sara"`

---

## How It Works

```
mic → 1.5s chunks → faster-whisper tiny (int8)
    → transcribe → check for "sara"
    → match → SARA activates → listen()
```

- Silent frames skipped (`mean amplitude < 0.002`) to save CPU
- `condition_on_previous_text=False` — each chunk evaluated independently
- Same `WhisperModel` instance as main STT — loaded once, shared

---

## Config (in `wake_word.py`)

```python
WAKE_PHRASES  = ["sara", "hey sara", "hey, sara"]   # add more if needed
CHUNK_SECONDS = 1.5    # listen window length
```

---

## Why faster-whisper instead of a keyword model

- **Zero setup** — no training, no API key, no custom model files
- **Exact name** — whisper knows "SARA", no phonetic approximation needed
- **Already installed** — same model used for command transcription
- **Tradeoff** — slightly more CPU than a dedicated wake word model, but fine for a personal Mac assistant

---

## See Also

- [[ProactiveMode]] · [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
