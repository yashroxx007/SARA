# SARA — Project Context

> Drop this file into any new chat session to get up to speed instantly.

---

## What Is This

SARA is a local, voice-first AI assistant for macOS built by Yash. It's not a chatbot — it's an operator. Think FRIDAY from Iron Man. It runs continuously, listens for a wake word, processes voice commands, acts on them using tools, and responds via TTS.

**GitHub:** https://github.com/yashroxx007/SARA  
**Location:** `~/SARA`  
**Run:** `cd ~/SARA && source .venv-1/bin/activate && python main.py`

---

## Stack

| Layer | Tech | Notes |
|---|---|---|
| STT | `faster-whisper` tiny, int8 | ~4x faster than whisper base |
| Brain | Claude API `claude-sonnet-4-6` | Tool use, 300 max_tokens |
| TTS | Kokoro ONNX `af_sarah` | Voice: af_sarah, speed 1.0 |
| VAD | `webrtcvad` aggressiveness 2 | ~800ms silence cutoff |
| Wake word | `faster-whisper` | Say "Hey SARA" — no external model |
| Memory | `memory.json` | Rolling 20 exchanges + summary |
| Python | 3.14, venv `.venv-1` | Other .venv and .venv-2 are dead |

---

## Project Structure

```
main.py                    — Everything: voice loop, Claude brain, tool dispatcher
src/
  tools/
    weather.py             — wttr.in, no key needed
    notes.py               — macOS Notes via AppleScript
    reminders.py           — macOS Reminders via AppleScript (date bug fixed)
    datetime_tool.py       — Returns current date/time string
    mac_control.py         — Volume, brightness, open/quit apps, lock, trash
    web_search.py          — DuckDuckGo Instant Answers, no key needed
    file_manager.py        — find_file, open_file, reveal_in_finder, list_folder
    calendar_tool.py       — macOS Calendar via AppleScript
    system_stats.py        — CPU/RAM/battery/disk via psutil
    spotify.py             — AppleScript controls + optional Web API search
    timer.py               — Background thread countdown, speaks when done
    messaging.py           — iMessage/SMS via Messages AppleScript
    screen_context.py      — screencapture → base64 → Claude vision
  core/
    wake_word.py           — faster-whisper based "Hey SARA" detection
    proactive.py           — Background thread: 8am briefing, meeting alerts, 6pm wrap
  brain/agent.py           — Empty stub
  memory/context.py        — Empty stub
  voice/input.py           — Empty stub
  voice/output.py          — Empty stub
docs/                      — Obsidian vault (19 .md files, feature docs + roadmap)
memory.json                — Persistent conversation history (gitignored)
memory_summary.json        — Auto-generated summary of old exchanges (gitignored)
.env                       — ANTHROPIC_API_KEY (gitignored)
kokoro-v1.0.onnx           — TTS model (gitignored, ~310MB)
voices-v1.0.bin            — TTS voices (gitignored, ~27MB)
```

---

## All Active Tools (14 registered in main.py)

| Tool name | What it does |
|---|---|
| `get_current_datetime` | Returns current date/time — called before reminders/calendar |
| `get_weather` | Current weather via wttr.in |
| `create_note` | Saves to macOS Notes app |
| `create_reminder` | Creates macOS reminder with optional due date |
| `mac_control` | Volume, brightness, open/quit apps, lock screen, empty trash |
| `web_search` | DuckDuckGo instant answers |
| `file_manager` | Find, open, list files on disk |
| `calendar` | Read today/upcoming events, create events |
| `system_stats` | CPU, RAM, battery, disk, top processes |
| `spotify` | Play, pause, skip, volume, current track, search |
| `timer` | Countdown timer — calls speak() when done |
| `messaging` | iMessage/SMS via Messages.app — always confirms before sending |
| `screen_context` | Screenshot → Claude vision → spoken description |

---

## Key Implementation Details

### Date Locale (important)
macOS on this machine uses **DD/MM/YYYY** (Indian English locale). AppleScript's `date` literal fails with `"June 10, 2026 09:00:00"`. All tools that set dates (`reminders.py`, `calendar_tool.py`) parse with Python `datetime` and reformat to `DD/MM/YYYY HH:MM AM/PM` before passing to AppleScript.

### Wake Word
`src/core/wake_word.py` streams mic in 1.5s chunks → transcribes with faster-whisper tiny → checks if "sara" or "hey sara" is in the text. No external model. Say **"Hey SARA"** to activate.

### Memory Summarisation
When `conversation_history` exceeds 30 exchanges, `maybe_summarise()` compresses the oldest ones via `claude-haiku-4-5` into `memory_summary.json`. The summary is injected into every system prompt. Keeps last 10 exchanges verbatim.

### Proactive Mode
`src/core/proactive.py` runs as a daemon thread. Wakes every minute. Fires:
- 8:00 AM → morning briefing (weather + calendar)
- Every minute → checks for meetings starting in ~15 min
- 18:00 → evening wrap

### Timer
`src/tools/timer.py` uses `speak()` injected at startup via `set_speak(speak)`. Fires in a daemon thread — `time.sleep(minutes * 60)` then calls speak.

### Tool Dispatcher Pattern
`main.py → think()` — all tool handling is a single `if/elif` chain. When adding a new tool: (1) write the function in `src/tools/`, (2) import at top of main.py, (3) add tool definition to the `tools=[]` list in `client.messages.create()`, (4) add `elif tool_name == "..."` branch in the dispatcher.

### Subprocess Pattern
All AppleScript tools use:
```python
result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
if result.returncode != 0:
    return f"Error: {result.stderr.strip()}"
```
Never use `subprocess.run` without `capture_output=True` — errors were silently swallowed before.

---

## Environment

```
File: ~/SARA/.env
ANTHROPIC_API_KEY=...           (required)
SPOTIFY_TOKEN=...               (optional — enables play_track search)
```

---

## Known Issues / Gotchas

- `set_brightness` in `mac_control.py` requires Accessibility permission (System Settings → Privacy → Accessibility). Falls back to `brightness` CLI if `System Events` fails.
- Spotify `play_track` opens URI search without `SPOTIFY_TOKEN` — doesn't auto-play
- iMessage contact name must match exactly as stored in Contacts
- `screen_context` captures primary display only
- `file_manager.find_file` uses glob (slow on large dirs) — could swap to `mdfind` for instant Spotlight results
- Calendar `create_event` defaults to `"Home"` calendar — update if that doesn't exist on the machine
- Wake word uses 1.5s listen windows — there's a ~1.5s detection delay by design

---

## Roadmap (remaining)

Nothing critical left. Nice-to-haves:
- Custom "Hey SARA" wake word model (train with openWakeWord, ~20 voice samples)
- `mdfind` instead of glob in `file_manager.find_file`
- Spotify Web API token setup for full `play_track`
- `cancel_timer(label)` and `list_timers()`
- `read_note(title)` — read notes back by voice
- Multi-monitor support in `screen_context`

---

## Version History (short)

| Version | What |
|---|---|
| 0.1 | Whisper + Claude + Kokoro + webrtcvad + memory |
| 0.2 | Weather, Notes, Reminders tools |
| 0.2.1 | Reminders date bug fix, FP16 warning fix, error handling |
| 0.3 | DateTime tool |
| 0.4 | Mac Control, Web Search, File Manager, Calendar, System Stats, Spotify, Timer |
| 0.5 | Faster STT, Memory summarisation, iMessage, Screen Context, Proactive mode, Wake word |
| 0.5.1 | Switched wake word from pvporcupine (paid) → openWakeWord (free) |
| 0.5.2 | Switched wake word to faster-whisper — native "Hey SARA", zero setup |
