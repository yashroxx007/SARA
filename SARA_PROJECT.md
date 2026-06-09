# SARA — SR's Autonomous Response Assistant

## What is SARA
A fully local, voice-activated AI assistant built on a MacBook Air M5 15" (16GB/512GB, macOS Tahoe 26.5.1). Responds via female voice, executes tasks autonomously when prompted. Think Friday from Iron Man — personal, capable, always available.

---

## Hardware
| Spec | Detail |
|---|---|
| Machine | MacBook Air M5 15" |
| RAM | 16GB Unified Memory |
| Storage | 512GB SSD |
| OS | macOS Tahoe 26.5.1 |
| Machine Name | sr |
| Username | yash |

---

## Core Stack
| Component | Tool | Purpose |
|---|---|---|
| Brain | Gemma 4 via Ollama | Fully local, offline capable |
| Voice Input | OpenAI Whisper | Local speech to text |
| Voice Output | Kokoro TTS | Local, female voice |
| Agent Framework | LangChain | Autonomous task execution |
| Working Memory | ChromaDB | Vector search, semantic recall |
| Readable Logs | Obsidian Vault | Human-readable conversation logs |
| Mac Control | AppleScript + Python | System automation |
| Cost | Zero | Fully free stack |

> **Note:** CrewAI removed — it's a multi-agent coordination framework with no role in a single-agent assistant. LangChain alone handles tool use.

---

## Project Structure
```
~/SARA/
├── main.py               # Entry point
├── requirements.txt      # Dependencies
├── .env                  # Environment variables
├── README.md             # Project docs
└── src/
    ├── __init__.py
    ├── voice/
    │   ├── input.py      # Whisper — speech to text
    │   └── output.py     # Kokoro — text to speech
    ├── brain/
    │   └── agent.py      # Gemma 4 + LangChain thinking
    ├── tools/
    │   ├── mac_control.py    # AppleScript Mac automation
    │   ├── web_search.py     # DuckDuckGo free search
    │   └── file_manager.py   # File operations
    └── memory/
        └── context.py    # ChromaDB + Obsidian logging
```

---

## Memory Architecture
- **ChromaDB** — SARA's working memory (semantic vector search, fast recall)
- **Obsidian** — SARA's readable logs (every conversation logged as .md, human inspectable)

SARA thinks with ChromaDB. Yash reads with Obsidian.

---

## Build Roadmap
| Phase | Timeline | Goal |
|---|---|---|
| Week 1 | Now | Bare loop: mic → Whisper → Ollama → Kokoro → speaker. No frameworks. Target: <3s response time. |
| Week 2 | Week 2 | Add LangChain. Mac control tools via AppleScript. |
| Week 3 | Week 3 | Web search + summarisation |
| Week 4 | Week 4 | ChromaDB memory + Obsidian logging |
| Month 2-3 | Later | Autonomous multi-step agents |

---

## Installed & Verified
- [x] Ollama + Gemma 4
- [x] OpenAI Whisper
- [x] Kokoro TTS
- [x] Portaudio + Sounddevice
- [x] Homebrew
- [ ] Python 3.10+ (⚠️ system Python is 3.9 — LangChain and ChromaDB require 3.10+. Set up a 3.10+ venv before proceeding.)
- [ ] LangChain
- [ ] ChromaDB

---

## Builder Context
**Yash (SR)** — Data Analyst, founder phase, building SARA as primary AI infrastructure for work and side ventures. Direct communication style, structured builds, zero unnecessary cost. MacBook Air M5 is the primary machine for this entire founder phase.

---

## Naming
**S.A.R.A.** = SR's Autonomous Response Assistant  
Named after builder's initials. Female voice. Friday-inspired. Built to grow.
