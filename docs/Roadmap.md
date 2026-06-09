# Roadmap

> Ordered by impact. Think FRIDAY, not Siri.

---

## 🔴 High Priority

### Wake Word — "Hey SARA"
- **What:** Always-on listening; no push-to-talk
- **How:** `pvporcupine` (Picovoice) — runs on-device, low CPU
- **Why now:** Biggest UX gap. Currently need to trigger manually.
- **Files to change:** `main.py` listen loop
- **Effort:** Medium

### Faster STT
- **What:** Cut transcription latency from ~2s to ~0.5s
- **How:** Swap `whisper base` → `faster-whisper` with `tiny` or `small` model
- **Why now:** Every voice command feels sluggish. This is the #1 feel improvement.
- **Files to change:** `main.py` — `listen()`, model init
- **Effort:** Low

---

## 🟡 Medium Priority

### Proactive Mode
- **What:** SARA speaks unprompted — morning briefing, calendar alerts, reminders
- **How:** Background thread checks time + calendar every minute; calls `speak()` when needed
- **Examples:**
  - "Good morning. You have 3 meetings today. First one's at 10."
  - "Heads up, your 3pm meeting starts in 15 minutes."
- **Files:** New `src/core/proactive.py`, injected into `main.py`
- **Effort:** Medium

### iMessage / WhatsApp
- **What:** Send messages by voice — "Tell Arjun I'm on my way"
- **How:** iMessage via AppleScript; WhatsApp via `open whatsapp://` URL scheme
- **Files:** New `src/tools/messaging.py`
- **Effort:** Medium
- **Note:** Will ask for confirmation before sending

### Spotify Token / Full Search
- **What:** `play_track` currently falls back to URI search if no token; full search needs a Spotify API token
- **How:** Add `SPOTIFY_TOKEN` to `.env`, or implement PKCE flow once
- **Files:** `src/tools/spotify.py`
- **Effort:** Low (once token is obtained)

---

## 🟢 Lower Priority

### Screen Context (Vision)
- **What:** "SARA, what's on my screen?" — screenshot → Claude vision → spoken description
- **How:** `screencapture` CLI → base64 → Claude `image` content block
- **Files:** New `src/tools/screen.py`
- **Effort:** Low (Claude already supports vision)

### Memory Summarisation
- **What:** Instead of truncating at 20 exchanges, summarise old history and keep a running summary
- **How:** When history > 20, ask Claude to summarise oldest 10 exchanges into 2-3 sentences; store as system context
- **Files:** `main.py` — `save_memory`, `load_memory`, `think()`
- **Why:** Longer context without growing token cost
- **Effort:** Low

### WhatsApp Voice Note Transcription
- **What:** Transcribe voice notes from WhatsApp and feed to SARA for action
- **Effort:** High (depends on WhatsApp API access)

### Custom Wake Phrase
- **What:** Let Yash set his own wake phrase beyond "Hey SARA"
- **Effort:** Low (Porcupine supports custom keywords with their SDK)

### Multi-Tool Chaining
- **What:** Claude already does this, but handle cases where one tool result feeds another in a single turn
- **Example:** "Find my resume and email it to Arjun" — find_file → then messaging
- **Effort:** Medium

---

## ✅ Completed

- [x] Whisper STT
- [x] Kokoro TTS
- [x] webrtcvad silence detection
- [x] Claude tool use
- [x] Persistent memory
- [x] Weather tool
- [x] Notes tool
- [x] Reminders tool (+ date bug fix)
- [x] DateTime tool (no more asking "what time is it?")
- [x] FP16 warning fix
- [x] Mac Control (volume, brightness, apps, lock)
- [x] Web Search (DuckDuckGo Instant Answers)
- [x] File Manager (find, open, reveal, list)
- [x] Calendar (read today/upcoming, create events)
- [x] System Stats (CPU, RAM, battery, disk, top procs)
- [x] Spotify (play/pause/skip/volume/search)
- [x] Timer (background thread, speaks when done)
- [x] Faster STT — faster-whisper tiny int8 (~4x faster)
- [x] Memory summarisation — compresses at 30 exchanges
- [x] iMessage / SMS — via Messages app AppleScript
- [x] Screen context — screenshot → Claude vision
- [x] Proactive mode — 8am briefing, meeting alerts, 6pm wrap
- [x] Wake word — pvporcupine (needs PICOVOICE_KEY in .env)

---

## See Also

- [[SARA]] — overview
- [[Status]] — current health
- [[Changelog]] — what's been done
