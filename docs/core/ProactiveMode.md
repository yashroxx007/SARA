# Core — Proactive Mode

**Status:** ✅ Live  
**File:** `src/core/proactive.py`  
**Added:** v0.5.0

---

## What It Does

A background thread that monitors time and calendar, making SARA speak unprompted at the right moments — like a real operator, not just a reactive assistant.

---

## Triggers

| Time | What Happens |
|---|---|
| **8:00 AM** | Morning briefing — today's weather + schedule |
| **6:00 PM** | Evening wrap — summary of the day's events |
| **Every minute** | Checks for calendar events starting in ~10-15 mins → meeting alert |

---

## Example Outputs

> *"Morning, Yash. Partly cloudy, 27 degrees. You've got a standup at 10 and a client call at 3. No gaps till evening."*

> *"Heads up — your 3pm call starts in 15 minutes."*

> *"That's a wrap. You had three meetings today. Get some rest."*

---

## Architecture

```
proactive.init(speak, client, system_prompt)   # called at startup
proactive.start()                              # launches daemon thread

Thread wakes every minute (sleeps to next :00)
→ 8:00 AM  → _deliver_briefing("morning")
→ 18:00    → _deliver_briefing("evening")
→ every    → _check_upcoming_meetings()
```

- Thread is `daemon=True` — dies when main process exits
- Briefings use `claude-haiku-4-5` (fast + cheap for scheduled tasks)
- Meeting alerts use a two-step check: get events → ask Claude if any start in ~15 min

---

## Configuration

No config file needed. To change times, edit the `_check_and_speak()` function in `src/core/proactive.py`.

---

## Known Limitations

- Meeting alerts fire on a 1-minute polling loop — could miss a meeting if SARA is started late
- Briefing at 8am only triggers if SARA is already running at that time

---

## See Also

- [[WakeWord]] · [[../tools/Calendar]] · [[../tools/Weather]]
- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
