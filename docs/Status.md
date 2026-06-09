# Current Status

> Last updated: 9 June 2026 (v0.5.0)

---

## System Health

| Component | Status | Notes |
|---|---|---|
| STT (faster-whisper) | ✅ Working | `tiny` + `int8` + `beam_size=1` — ~4x faster |
| TTS (Kokoro) | ✅ Working | `af_sarah` voice |
| VAD | ✅ Working | ~800ms silence cutoff |
| Claude API | ✅ Working | `claude-sonnet-4-6`, tool use active |
| Memory | ✅ Working | Rolling 20-exchange JSON |
| Tool dispatcher | ✅ Working | 14 tools registered |
| Wake word | ✅ Ready | Needs `PICOVOICE_KEY` in `.env`; falls back to Enter key |
| Proactive mode | ✅ Working | Morning briefing 8am, meeting alerts, evening wrap 6pm |
| Memory summarisation | ✅ Working | Compresses at 30 exchanges, injects summary into system prompt |

---

## Tools Status

| Tool | Status | Last Tested |
|---|---|---|
| Weather | ✅ Live | — |
| Notes | ✅ Live | — |
| Reminders | ✅ Live | 9 Jun 2026 — date bug fixed |
| DateTime | ✅ Live | 9 Jun 2026 |
| Mac Control | ✅ Live | 9 Jun 2026 |
| Web Search | ✅ Live | 9 Jun 2026 |
| File Manager | ✅ Live | 9 Jun 2026 |
| Calendar | ✅ Live | 9 Jun 2026 |
| System Stats | ✅ Live | 9 Jun 2026 |
| Spotify | ✅ Live | 9 Jun 2026 |
| Timer | ✅ Live | 9 Jun 2026 |
| iMessage / SMS | ✅ Live | 9 Jun 2026 |
| Screen Context | ✅ Live | 9 Jun 2026 |

---

## Known Issues

- `mac_control` brightness fallback only works if `brightness` CLI is installed (`brew install brightness`)
- Spotify `play_track` search requires `SPOTIFY_TOKEN` in `.env`; without it, falls back to opening a Spotify URI search
- `web_search` uses DuckDuckGo Instant Answers — works well for facts/people, weak on recent news
- `file_manager` find_file skips `Library/` and `.Trash` but can be slow on large home dirs
- Multi-step tool calls (e.g. "set a reminder for tomorrow at 9") require two tool calls in sequence — Claude handles this correctly
- Wake word uses `"hey siri"` built-in keyword (closest phonetically) — can be replaced with a custom "Hey SARA" keyword via Picovoice Console (paid or custom tier)
- `screen_context` captures the full display — on multi-monitor setups it captures only the primary screen

---

## Environment

```
Python:    3.14 (.venv-1)
Model:     claude-sonnet-4-6
Whisper:   base
Kokoro:    v1.0 ONNX
Platform:  macOS (Apple Silicon)
Locale:    DD/MM/YYYY (Indian English)
```

---

## See Also

- [[SARA]] — full overview
- [[Changelog]] — what changed and when
- [[Roadmap]] — what's next
