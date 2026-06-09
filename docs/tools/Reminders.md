# Tool — Reminders

**Status:** ✅ Live  
**File:** `src/tools/reminders.py`  
**Added:** v0.2.0 · **Bug fixed:** v0.2.1

---

## What It Does

Creates reminders in the macOS Reminders app via AppleScript. Supports optional due date and notes.

---

## Voice Commands

- *"Remind me to call Arjun tomorrow at 9"*
- *"Set a reminder for the standup at 10am"*
- *"Remind me to take medication at 8pm"*

---

## Function

```python
create_reminder(title: str, notes: str = "", due_date: str | None = None) -> str
```

**`due_date` format:** `"June 10, 2026 09:00:00"` — Claude always uses this format; the tool handles conversion internally.

---

## The Bug (v0.2.1 fix)

**Root cause:** macOS locale is DD/MM/YYYY (Indian English). AppleScript's `date` literal couldn't parse `"June 10, 2026 09:00:00"` — it's a compile-time syntax error, so the *entire script* aborted before the reminder was even created. The function still returned `"Reminder created"` because there was no error checking.

**Fix:**
1. Parse Claude's date string with Python `datetime`
2. Reformat to `DD/MM/YYYY HH:MM AM/PM` before embedding in AppleScript
3. Added `capture_output=True` + `returncode` check — returns the actual error if something fails
4. Escape `"` and `\` in title/notes to prevent AppleScript injection

---

## Implementation Notes

- List: `"Reminders"` (confirmed to exist on this machine)
- Date parsing tries 3 formats: `%B %d, %Y %H:%M:%S` → `%B %d, %Y %H:%M` → `%B %d, %Y`

---

## See Also

- [[DateTime]] — paired tool; Claude calls this before creating reminders so it knows the current date
- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
