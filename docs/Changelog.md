# Changelog

All notable changes to SARA, in reverse chronological order.

---

## [0.6.1] — 11 June 2026 — Project Knowledge

### Added
- **Projects tool** (`src/tools/projects.py`) — SARA now knows what Yash is building across all his work, not just SARA itself.
  - `projects/` folder in repo root: one markdown file per project (instagram-content, digital-product-app, sara)
  - `list_projects`, `get_project` (fuzzy name match — "the app project" works), `update_project` (timestamped log entries by voice), `create_project`
  - System prompt instructs SARA to pull project context when Yash mentions working on something, and to log progress/decisions proactively
  - Cross-Claude bridge: other repos' CLAUDE.md files can instruct Claude Code to update `~/SARA/projects/<name>.md` at session end — knowledge flows from any Claude surface into SARA
  - Token-efficient by design: project context loads on demand via tool, not injected into every turn

---

## [0.6.0] — 11 June 2026 — Resilience + Token Overhaul

### Fixed
- **SARA no longer dies when anything fails.** Every failure path now speaks instead of crashing:
  - Tool exceptions → caught in `dispatch_tool()`, returned as `tool_result` with `is_error: True` so Claude explains what broke
  - API errors (rate limit, network, 5xx) → caught in main loop, SARA says what's wrong
  - Mic/stream errors → caught around `listen()`, "Mic glitched, Boss"
  - Wake word errors → logged, 2s backoff, retry
  - `sanitize_history` now also strips dangling `tool_use` blocks from a trailing assistant message (crash-recovery artifact that caused 400s)

### Changed
- **Prompt caching enabled** — `cache_control: ephemeral` on the static system prompt block. Tools schema + system prompt (~3.5K tokens) now cached: cache reads cost 10% of base price and don't count toward the input-token rate limit (which we hit at 105% on Jun 9). Memory block sits after the breakpoint so summary updates don't invalidate the cache.
- **Dispatcher rewritten as a registry** — `TOOL_HANDLERS` dict + `_action_tool()` wrapper replaces the 70-line if/elif chain. Adding a tool is now one schema entry + one handler line.
- `TOOLS_SCHEMA` moved to module level (built once, not per call)
- `_call_claude()` helper deduplicates the two API call sites
- **Tool loop circuit breaker** — max 8 rounds per turn so a confused model can't loop forever

### Architecture
- `think()` is now ~50 lines (was ~200)
- Failure philosophy: the voice loop is sacred — nothing propagates an exception past it

---

## [0.5.4] — 10 June 2026 — Fenced Memory Injection

### Added
- **`src/memory/context.py`** — new module for memory context fencing (was a stub).
  - `sanitize_context()` strips any `<memory-context>` tags, system notes, and full fenced blocks from raw summary text before wrapping — a poisoned memory cannot escape its fence and impersonate fresh instructions.
  - `build_memory_block()` wraps the sanitized summary in a `<memory-context>` block with an inline system note so the model treats it as reference data, not new user input.

### Changed
- **`main.py`** — fenced memory injection replaces the previous plain string concatenation.
  - Old: `system += f"\n\nContext from earlier conversations:\n{summary}"`
  - New: `system += "\n\n" + build_memory_block(summary)` — sanitized and fenced.
  - Pattern adopted from [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent).

### Security
- Closes injection vector where a prior conversation containing prompt-injection text could re-enter the system prompt verbatim and impersonate instructions on every subsequent turn.

---

## [0.5.3] — 9 June 2026 — Multi-Step Tool Chaining Fix

### Fixed
- **IndexError on chained tool calls** — `think()` previously handled only one tool call per turn. If Claude chained tools (e.g. `get_current_datetime` → `create_reminder`, or `system_stats` → `web_search`), the follow-up response was another `tool_use` block, and `follow_up.content[0].text` crashed with `IndexError: list index out of range`.
- Refactored `think()` to use a `while response.stop_reason == "tool_use"` loop. Runs all tool_use blocks in a single response (batch), appends results, re-calls Claude, repeats until `stop_reason == "end_turn"`.
- Extracted `tools=[...]` into a local `tools_schema` variable — reused by both the initial call and every loop iteration.
- Reply extraction changed from `response.content[0].text` to `next((b.text for b in response.content if hasattr(b, "text")), fallback)` — safe against edge-case empty text blocks.

---

## [0.5.2] — 9 June 2026 — Wake Word: "Hey SARA"

### Changed
- Dropped openWakeWord (no built-in "sara" model) in favour of **faster-whisper** for wake detection
- Say **"Hey SARA"** or just **"SARA"** — exact name, zero training, zero setup
- Reuses the same `WhisperModel` instance already loaded for STT
- Silent frames skipped to reduce unnecessary CPU usage

---

## [0.5.1] — 9 June 2026 — Wake Word Fix

### Changed
- Replaced `pvporcupine` (paid) with **openWakeWord** (free, open source, Apache 2.0)
- Wake word is now `hey_jarvis` — say "Hey Jarvis" to activate
- No API key, no account, no cost — models download once and run fully on-device
- Removed `PICOVOICE_KEY` from `.env`
- Custom "Hey SARA" model can be trained and swapped in — see [[core/WakeWord]]

---

## [0.5.0] — 9 June 2026 — Brain Upgrades

### Added
- **Faster STT** — swapped `whisper base` → `faster-whisper tiny` with `int8` quantisation, `beam_size=1`, and built-in VAD filter. ~4x faster transcription.
- **Memory Summarisation** — when history exceeds 30 exchanges, the oldest ones are compressed into a running summary via `claude-haiku-4-5`. Summary is injected into the system prompt on every turn. Keeps last 10 exchanges verbatim.
- **iMessage / SMS** (`src/tools/messaging.py`) — send messages via macOS Messages app. Claude always confirms before sending.
- **Screen Context** (`src/tools/screen_context.py`) — `screencapture` → base64 → Claude vision. SARA can describe, summarise, or read anything on screen.
- **Proactive Mode** (`src/core/proactive.py`) — background thread wakes every minute. Delivers: 8am morning briefing (weather + calendar), 6pm evening wrap, 15-min meeting alerts.
- **Wake Word** (`src/core/wake_word.py`) — `pvporcupine` integration. Uses "hey siri" built-in keyword until a custom "Hey SARA" model is created. Falls back to Enter-key if `PICOVOICE_KEY` not set.

### Changed
- Main loop now calls `wait_for_wake_word()` before each `listen()` — hands-free when key is configured
- `.env` now has `PICOVOICE_KEY=` placeholder

### Dependencies Added
- `faster-whisper`
- `pvporcupine`

---

## [0.4.0] — 9 June 2026 — FRIDAY Expansion

### Added
- **Mac Control** (`src/tools/mac_control.py`)
  - Volume: `set_volume`, `mute`, `unmute`
  - Brightness: `set_brightness`
  - Apps: `open_app`, `quit_app`
  - System: `lock_screen`, `empty_trash`
- **Web Search** (`src/tools/web_search.py`)
  - DuckDuckGo Instant Answers (no API key needed)
  - Falls back to related topics if no abstract found
- **File Manager** (`src/tools/file_manager.py`)
  - `find_file` — recursive glob across home dir
  - `open_file` — open with default app
  - `reveal_in_finder` — show in Finder
  - `list_folder` — list directory contents
- **Calendar** (`src/tools/calendar_tool.py`)
  - `get_todays_events` — today's schedule
  - `get_upcoming_events` — next N days
  - `create_event` — new calendar event
- **System Stats** (`src/tools/system_stats.py`)
  - CPU, RAM, battery via `psutil`
  - Top processes by CPU
  - Disk usage
- **Spotify** (`src/tools/spotify.py`)
  - Play, pause, next, previous
  - Get current track
  - Set Spotify volume
  - Play by track name (with optional `SPOTIFY_TOKEN`)
- **Timer** (`src/tools/timer.py`)
  - Background thread countdown
  - SARA speaks aloud when timer fires
  - Injected `speak()` reference at startup

### Dependencies Added
- `psutil` (installed into `.venv-1`)

---

## [0.3.0] — 9 June 2026 — DateTime Tool

### Added
- **DateTime** (`src/tools/datetime_tool.py`)
  - Returns current date/time as a readable string
  - Claude instructed to call this before setting reminders — no more asking "what time is it?"

---

## [0.2.1] — 9 June 2026 — Bug Fixes

### Fixed
- **Reminders date bug** — AppleScript was receiving `"June 10, 2026 09:00:00"` but macOS locale is DD/MM/YYYY. Script errored silently and no reminder was created. Fixed by parsing with Python `datetime` and reformatting to `DD/MM/YYYY HH:MM AM/PM`.
- **FP16 warning** — Added `fp16=False` to `whisper_model.transcribe()`. Warning gone.
- **Silent subprocess failures** — All AppleScript tools now use `capture_output=True` and check `returncode`.
- **Input injection safety** — Title/notes fields now escape `"` and `\` before embedding in AppleScript strings.

---

## [0.2.0] — Initial Tool Set

### Added
- **Weather** — `wttr.in` API, city-based current conditions
- **Notes** — macOS Notes app via AppleScript
- **Reminders** — macOS Reminders app via AppleScript (later fixed in 0.2.1)

---

## [0.1.0] — Foundation

### Added
- Whisper STT with `webrtcvad` voice activity detection
- Claude API integration with tool use
- Kokoro ONNX TTS (`af_sarah` voice)
- Persistent memory via `memory.json`
- SARAH system prompt — calm, sharp, dry humour, voice-optimised
