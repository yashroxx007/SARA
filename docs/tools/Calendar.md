# Tool — Calendar

**Status:** ✅ Live  
**File:** `src/tools/calendar_tool.py`  
**Added:** v0.4.0

---

## What It Does

Read and create events in the macOS Calendar app via AppleScript.

---

## Voice Commands

| Say... | Action |
|---|---|
| *"What's on my schedule today?"* | `get_todays_events()` |
| *"What have I got this week?"* | `get_upcoming_events(days=7)` |
| *"Any meetings tomorrow?"* | `get_upcoming_events(days=2)` |
| *"Add a meeting with Rohan at 3pm tomorrow"* | `create_event(...)` |

---

## Functions

```python
get_todays_events() -> str
get_upcoming_events(days: int = 7) -> str
create_event(title: str, start: str, end: str, calendar: str = "Home") -> str
```

**Date format for `create_event`:** `"June 10, 2026 14:00:00"` — Claude uses this; tool converts internally to `DD/MM/YYYY HH:MM AM/PM` for AppleScript (same fix as Reminders).

---

## Implementation Notes

- Iterates over all calendars to find events in range
- Uses AppleScript's `start date >= startOfDay and start date <= endDate` filter
- `create_event` defaults to `"Home"` calendar — if that doesn't exist, AppleScript will error; update the default in the tool if needed
- Same date locale fix as [[Reminders]] — DD/MM/YYYY

---

## Known Issues

- Calendar name `"Home"` might not exist for all users — check Calendar.app and update default if needed
- Read-only event details for now — can get title + start time, not location/notes/attendees

---

## Planned Upgrades

- `delete_event(title)` — cancel meetings by voice
- `get_event_details(title)` — full details including attendees, location
- Natural language duration: *"1 hour"* → auto-calculate end time

---

## See Also

- [[DateTime]] — used for current date context when creating events
- [[Reminders]] — similar AppleScript pattern
- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
