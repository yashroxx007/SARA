# SARA — Voice AI Assistant

> A local, voice-first AI operator for macOS. Not a chatbot. An operator.  
> Built on Whisper STT · Claude API · Kokoro TTS · webrtcvad

---

## What SARA Can Do

| Category | Capabilities |
|---|---|
| **Mac Control** | Volume, brightness, open/quit apps, lock screen, empty trash |
| **Music** | Spotify play/pause/skip/search via voice |
| **Calendar** | Read schedule, create events |
| **Reminders** | Set reminders with natural due dates |
| **Notes** | Save notes to macOS Notes app |
| **Files** | Find, open, list files by voice |
| **Web Search** | Real-time answers via DuckDuckGo |
| **System** | CPU, RAM, battery, disk, top processes |
| **Messaging** | Send iMessage / SMS (with confirmation) |
| **Screen** | Describe what's on screen using vision |
| **Timer** | Countdown timers — SARA speaks when done |
| **Weather** | Current conditions for any city |
| **Proactive** | Morning briefings, meeting alerts, evening wrap |
| **Memory** | Persistent across sessions, auto-summarised |

---

## Stack

| Layer | Technology |
|---|---|
| STT | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (`tiny`, `int8`) |
| Brain | [Claude API](https://docs.anthropic.com) (`claude-sonnet-4-6`) |
| TTS | [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx) (`af_sarah` voice) |
| VAD | `webrtcvad` |
| Wake word | faster-whisper — say **"Hey SARA"** |
| Memory | Rolling JSON + auto-summarisation via `claude-haiku` |

---

## Setup

### 1. Clone

```bash
git clone https://github.com/yashroxx007/SARA.git
cd SARA
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Download model files

SARA needs two large files that aren't in the repo (too big for git):

| File | Source |
|---|---|
| `kokoro-v1.0.onnx` | [Kokoro ONNX releases](https://github.com/thewh1teagle/kokoro-onnx/releases) |
| `voices-v1.0.bin` | Same release page |

Place both in the project root.

### 4. Add your API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 5. Run

```bash
python main.py
```

Say **"Hey SARA"** to activate.

---

## Environment Variables

```env
ANTHROPIC_API_KEY=your_key_here
SPOTIFY_TOKEN=optional_for_track_search
```

---

## Project Structure

```
main.py                  — Voice loop, Claude brain, tool dispatcher
src/
  tools/
    weather.py           — wttr.in weather
    notes.py             — macOS Notes via AppleScript
    reminders.py         — macOS Reminders via AppleScript
    datetime_tool.py     — Current date/time
    mac_control.py       — Volume, brightness, apps
    web_search.py        — DuckDuckGo instant answers
    file_manager.py      — Find, open, list files
    calendar_tool.py     — macOS Calendar via AppleScript
    system_stats.py      — CPU, RAM, battery (psutil)
    spotify.py           — Spotify via AppleScript
    timer.py             — Background countdown timers
    messaging.py         — iMessage / SMS via AppleScript
    screen_context.py    — Screenshot → Claude vision
  core/
    proactive.py         — Background briefings + meeting alerts
    wake_word.py         — "Hey SARA" detection via faster-whisper
docs/                    — Obsidian vault (feature docs, roadmap, changelog)
```

---

## Voice Commands (examples)

```
"Hey SARA, set volume to 60"
"Hey SARA, what's on my schedule today?"
"Hey SARA, remind me to call Arjun tomorrow at 9am"
"Hey SARA, play something on Spotify"
"Hey SARA, how's the Mac doing?"
"Hey SARA, what's on my screen?"
"Hey SARA, set a 25 minute Pomodoro"
"Hey SARA, find my resume"
"Hey SARA, who is Sam Altman?"
"Hey SARA, tell Mum I'll be home by 8"
```

---

## Docs

Full feature docs, roadmap, and changelog live in [`/docs`](./docs) — open as an Obsidian vault for best experience.

---

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.10+
- Microphone + speakers
- Anthropic API key ([get one here](https://console.anthropic.com))
- Spotify desktop app (for music controls)
- macOS Accessibility permission (for brightness + lock screen)

---

## License

MIT
