# Tool — File Manager

**Status:** ✅ Live  
**File:** `src/tools/file_manager.py`  
**Added:** v0.4.0

---

## What It Does

Find, open, and inspect files on the Mac by voice.

---

## Voice Commands

| Say... | Action |
|---|---|
| *"Find my resume"* | `find_file("resume")` |
| *"Find that pitch deck PDF"* | `find_file("pitch deck", search_dir="~/Desktop")` |
| *"Open that file"* (after finding) | `open_file(path)` |
| *"Show it in Finder"* | `reveal_in_finder(path)` |
| *"What's on my Desktop?"* | `list_folder("~/Desktop")` |
| *"List my Downloads"* | `list_folder("~/Downloads")` |

---

## Functions

```python
find_file(name: str, search_dir: str = "~") -> str
open_file(path: str) -> str
reveal_in_finder(path: str) -> str
list_folder(path: str = "~/Desktop") -> str
```

---

## Implementation Notes

- `find_file` uses `glob` with `**/*name*` pattern — recursive
- Skips `/.Trash` and `/Library/` for speed
- Returns max 8 matches to keep response concise
- `open_file` uses `open` (macOS default app association)
- `reveal_in_finder` uses `open -R`

---

## Known Limitations

- `find_file` can be slow on very large home dirs — no index like Spotlight
- Case-insensitive matching only on case-insensitive filesystems (default macOS HFS+)

---

## Planned Upgrade

- Use `mdfind` (Spotlight CLI) instead of glob for instant results: `mdfind -name {query}`

---

## See Also

- [[MacControl]] — open apps by name
- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
