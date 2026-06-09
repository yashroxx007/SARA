# Tool — Notes

**Status:** ✅ Live  
**File:** `src/tools/notes.py`  
**Added:** v0.2.0

---

## What It Does

Creates notes in the macOS Notes app via AppleScript. Notes land in the default "Notes" folder.

---

## Voice Commands

- *"Take a note — [content]"*
- *"Remember this: [content]"*
- *"Save a note about [topic]"*

---

## Function

```python
create_note(title: str, body: str) -> str
```

---

## Implementation

AppleScript:
```applescript
tell application "Notes"
    make new note at folder "Notes" with properties {name: title, body: body}
end tell
```

---

## Known Limitations

- Write-only — can't read back notes yet (roadmap item)
- No folder selection — always saves to "Notes"

---

## Planned Upgrades

- `read_note(title)` — search and read back a note by name
- `list_notes()` — list recent notes

---

## See Also

- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
