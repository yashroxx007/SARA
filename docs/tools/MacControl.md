# Tool — Mac Control

**Status:** ✅ Live  
**File:** `src/tools/mac_control.py`  
**Added:** v0.4.0

---

## What It Does

Direct control over macOS system functions — volume, brightness, apps, and system actions.

---

## Voice Commands

| Say... | Action |
|---|---|
| *"Volume to 60"* / *"Turn it up"* | `set_volume(level)` |
| *"Mute"* | `mute()` |
| *"Unmute"* / *"Turn sound back on"* | `unmute()` |
| *"Brightness to 40"* | `set_brightness(level)` |
| *"Open Spotify"* / *"Launch Chrome"* | `open_app(name)` |
| *"Quit Safari"* / *"Close Slack"* | `quit_app(name)` |
| *"Lock the screen"* | `lock_screen()` |
| *"Empty the trash"* | `empty_trash()` |

---

## Functions

```python
set_volume(level: int)       # 0–100
mute()
unmute()
set_brightness(level: int)   # 0–100
open_app(app_name: str)
quit_app(app_name: str)
lock_screen()
empty_trash()
```

---

## Implementation Notes

- Volume uses `osascript` `set volume output volume`
- Brightness uses `System Events` display property; falls back to `brightness` CLI if that fails
- App open/quit use `open -a` and AppleScript `quit`
- Lock screen sends `Ctrl+Cmd+Q` via `System Events`

---

## Known Issues / Notes

- **Brightness:** `System Events` brightness control may require Accessibility permission. If it fails, install `brightness` CLI: `brew install brightness`
- **Lock screen:** Uses keyboard shortcut via `System Events` — requires Accessibility access

---

## See Also

- [[Spotify]] — separate tool for Spotify-specific controls
- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
