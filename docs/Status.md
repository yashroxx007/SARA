# Current Status

> Last updated: 14 June 2026 (v0.7.0)

---

## System Health

| Component | Status | Notes |
|---|---|---|
| STT (faster-whisper) | ✅ Working | `tiny` + `int8` + `beam_size=1` — ~4x faster |
| TTS (Kokoro) | ✅ Working | `af_sarah` voice |
| VAD | ✅ Working | ~800ms silence cutoff |
| Brain (local MLX) | ✅ Working | Qwen2.5-Coder-14B-4bit via mlx-omni-server :8080 — tool-calling verified (v0.7.0); ~14s/response on M5 |
| Vision (hybrid) | ✅ Working | `screen_context` still on Claude — needs `ANTHROPIC_API_KEY` |
| Memory | ✅ Working | Rolling 15-exchange JSON, fenced injection (v0.5.4) |
| Tool dispatcher | ✅ Working | 14 tools, registry-based, error-isolated (v0.6.0) |
| Crash resilience | ✅ Working | Tool/API/mic failures all spoken, never fatal (v0.6.0) |
| Wake word | ✅ Working | faster-whisper sliding window — say "Hey SARA"; no key, no setup (v0.5.2) |
| Conversation mode | ✅ Working | Wake once, talk freely; sleeps on silence or "that's all" |
| Proactive mode | ✅ Working | Morning briefing 8am, meeting alerts, evening wrap 6pm |
| Memory summarisation | ✅ Working | Compresses at 20 exchanges, injects summary into system prompt |
| Project knowledge | ✅ Working | Reads live files/Obsidian vaults via source pointers (v0.6.1) |

---

## Tools Status

| Tool | Status | Last Tested |
|---|---|---|
| Weather | ✅ Live | 14 Jun 2026 — Open-Meteo forecast (current + multi-day, rain probability) |
| Notes | ✅ Live | — |
| Reminders | ✅ Live | 9 Jun 2026 — date bug fixed |
| DateTime | ✅ Live | 9 Jun 2026 |
| Mac Control | ✅ Live | 9 Jun 2026 |
| Web Search | ✅ Live | 9 Jun 2026 |
| File Manager | ✅ Live | 9 Jun 2026 |
| Calendar | ✅ Live | 9 Jun 2026 |
| System Stats | ✅ Live | 14 Jun 2026 — two-pass CPU sampling fix |
| Spotify | ✅ Live | 9 Jun 2026 |
| Timer | ✅ Live | 9 Jun 2026 |
| iMessage / SMS | ✅ Live | 9 Jun 2026 |
| Screen Context | ✅ Live | 9 Jun 2026 |
| Projects | ✅ Live | 14 Jun 2026 — Arisn + Instagram wired in via source pointers |

---

## Known Issues

- `mac_control` brightness fallback only works if `brightness` CLI is installed (`brew install brightness`)
- Spotify `play_track` search requires `SPOTIFY_TOKEN` in `.env`; without it, falls back to opening a Spotify URI search
- `web_search` uses DuckDuckGo Instant Answers — works well for facts/people, weak on recent news
- `file_manager` find_file skips `Library/` and `.Trash` but can be slow on large home dirs
- Multi-step tool chains fully supported — `think()` loops until Claude returns plain text (8-round circuit breaker)
- `screen_context` captures the full display — on multi-monitor setups it captures only the primary screen
- `projects` source reader caps each linked source at 8K chars (newest files first) to keep token cost sane — very large vaults get truncated with a notice

---

## Environment

```
Python:    3.14 (.venv-1)  ·  server venv: 3.12 (~/mlx-server)
Model:     Qwen2.5-Coder-14B-4bit (local MLX) · Claude for vision only
Server:    mlx-omni-server --port 8080
Whisper:   tiny (int8) via faster-whisper
Kokoro:    v1.0 ONNX
Platform:  macOS (Apple Silicon — M5)
Locale:    DD/MM/YYYY (Indian English)
```

---

## See Also

- [[SARA]] — full overview
- [[Changelog]] — what changed and when
- [[Roadmap]] — what's next
