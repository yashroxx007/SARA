# SARA — System Overview

> **S**ystem for **A**dvanced **R**easoning & **A**ction  
> Voice AI assistant built for Yash. Not a chatbot. An operator.

---

## Stack

| Layer | Technology |
|---|---|
| STT | OpenAI Whisper (`base` model, `fp16=False` for CPU) |
| Brain | Claude API (`claude-sonnet-4-6`, tool use) |
| TTS | Kokoro ONNX (`af_sarah` voice) |
| VAD | `webrtcvad` (aggressiveness 2) |
| Memory | `memory.json` — rolling 20-exchange history |
| Runtime | Python 3.14, `.venv-1` |

---

## How to Run

```bash
cd ~/SARA
source .venv-1/bin/activate
python main.py
```

---

## Active Tools

| Tool | File | Status |
|---|---|---|
| Weather | `src/tools/weather.py` | ✅ Live (Open-Meteo forecast) |
| Notes | `src/tools/notes.py` | ✅ Live |
| Reminders | `src/tools/reminders.py` | ✅ Live (date bug fixed) |
| DateTime | `src/tools/datetime_tool.py` | ✅ Live |
| Mac Control | `src/tools/mac_control.py` | ✅ Live |
| Web Search | `src/tools/web_search.py` | ✅ Live |
| File Manager | `src/tools/file_manager.py` | ✅ Live |
| Calendar | `src/tools/calendar_tool.py` | ✅ Live |
| System Stats | `src/tools/system_stats.py` | ✅ Live |
| Spotify | `src/tools/spotify.py` | ✅ Live |
| Timer | `src/tools/timer.py` | ✅ Live |
| iMessage / SMS | `src/tools/messaging.py` | ✅ Live |
| Screen Context | `src/tools/screen_context.py` | ✅ Live |
| Projects | `src/tools/projects.py` | ✅ Live |

---

## Planned Upgrades

| Feature | Priority | Notes |
|---|---|---|
| Wake word ("Hey SARA") | 🔴 High | `pvporcupine` |
| Faster STT | 🔴 High | `faster-whisper` tiny |
| iMessage / WhatsApp send | 🟡 Medium | AppleScript |
| Proactive mode | 🟡 Medium | Background thread, calendar briefings |
| Screen context (vision) | 🟢 Low | Screenshot → Claude vision |
| Memory summarisation | 🟢 Low | Compress old history |

---

## Key Files

```
main.py               — Brain, voice loop, tool dispatcher
src/tools/            — All tool implementations
src/voice/            — input.py, output.py (stubs, logic is in main.py)
src/memory/           — context.py — memory fencing (sanitize + build_memory_block)
src/brain/            — agent.py (stub)
memory.json           — Persistent conversation history
docs/                 — This vault
```

---

## Links

- [[Changelog]]
- [[Roadmap]]
- [[Status]]
- [[tools/Weather]] · [[tools/Notes]] · [[tools/Reminders]]
- [[tools/MacControl]] · [[tools/WebSearch]] · [[tools/FileManager]]
- [[tools/Calendar]] · [[tools/SystemStats]] · [[tools/Spotify]] · [[tools/Timer]]
- [[tools/Messaging]] · [[tools/ScreenContext]] · [[tools/Projects]]
