# Tool — Timer

**Status:** ✅ Live  
**File:** `src/tools/timer.py`  
**Added:** v0.4.0

---

## What It Does

Background countdown timer. SARA speaks aloud when it fires — no notification banners, just her voice.

---

## Voice Commands

- *"Set a 25-minute Pomodoro"*
- *"Timer for 10 minutes"*
- *"Remind me in 5 minutes"*
- *"Set a 90-second timer"* → `minutes=1.5`

---

## Function

```python
set_timer(minutes: float, label: str = "Timer") -> str
```

- `minutes` can be fractional — `0.5` = 30 seconds, `1.5` = 90 seconds
- `label` is spoken back when the timer fires: *"Pomodoro done. 25 minutes are up."*
- Returns immediately: *"Pomodoro set for 25 minutes. I'll let you know."*

---

## How It Works

1. `set_timer()` starts a `daemon=True` background thread and returns immediately
2. Thread sleeps for `minutes * 60` seconds
3. On wake: prints to console and calls `speak()` to announce via TTS
4. `speak` is injected at startup via `set_speak(speak)` in `main.py` — this is called right after Kokoro and the `speak` function are defined

---

## Implementation Notes

- `daemon=True` — thread dies if the main process exits, no zombie threads
- Multiple timers can run simultaneously
- No cancel mechanism yet (roadmap)

---

## Planned Upgrades

- `cancel_timer(label)` — cancel a running timer by name
- `list_timers()` — show active timers and time remaining

---

## See Also

- [[Reminders]] — for time-based reminders in the Reminders app (persists across sessions)
- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
