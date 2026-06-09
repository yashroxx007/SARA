# Tool — Messaging (iMessage / SMS)

**Status:** ✅ Live  
**File:** `src/tools/messaging.py`  
**Added:** v0.5.0

---

## What It Does

Send iMessages and SMS via the macOS Messages app using AppleScript.

---

## Voice Commands

- *"Tell Arjun I'm on my way"*
- *"Message Rohan that the call is at 4"*
- *"Text +91XXXXXXXX that I'll be late"*

> ⚠️ SARA will always **confirm before sending** — she'll say *"Should I send it?"* before the message goes out.

---

## Functions

```python
send_imessage(contact: str, message: str) -> str
send_sms(phone: str, message: str) -> str
```

- `contact` — name (as it appears in Contacts), Apple ID email, or phone number
- `send_imessage` tries `participant` first, falls back to `buddy` if that fails

---

## Implementation Notes

- Uses `tell application "Messages"` — Messages app must be signed in
- iMessage service selected via `service type = iMessage`
- SMS service selected via `service type = SMS` (requires iPhone continuity)
- Input is escaped to prevent AppleScript injection

---

## Known Limitations

- Contact name must match exactly as stored in Contacts or as an iMessage handle
- SMS requires Continuity (iPhone must be on the same Apple ID on the same network)
- No read receipt or delivery confirmation returned

---

## See Also

- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
