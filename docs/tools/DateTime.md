# Tool — DateTime

**Status:** ✅ Live  
**File:** `src/tools/datetime_tool.py`  
**Added:** v0.3.0

---

## What It Does

Returns the current date and time as a human-readable string. Exists so Claude never has to ask Yash what time it is when setting reminders or calendar events.

---

## Function

```python
get_current_datetime() -> str
# Returns e.g. "9 June 2026, 08:04 PM"
```

---

## Why This Exists

Before this tool, every time SARA needed to set a reminder for "tomorrow" or "next Monday," she'd ask: *"What's today's date?"* — frustrating and un-FRIDAY-like.

Claude's tool description explicitly says: *"Always call this before creating a reminder so you know today's date and time without asking Yash."*

---

## See Also

- [[Reminders]] · [[Calendar]]
- [[../SARA]] · [[../Changelog]]
