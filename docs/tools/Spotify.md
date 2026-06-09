# Tool — Spotify

**Status:** ✅ Live  
**File:** `src/tools/spotify.py`  
**Added:** v0.4.0

---

## What It Does

Full Spotify control via AppleScript + optional Spotify Web API for track search.

---

## Voice Commands

| Say... | Action |
|---|---|
| *"Play"* / *"Resume"* | `play()` |
| *"Pause"* / *"Stop the music"* | `pause()` |
| *"Next"* / *"Skip"* | `next_track()` |
| *"Previous"* / *"Go back"* | `previous_track()` |
| *"What's playing?"* | `get_current_track()` |
| *"Spotify volume to 70"* | `set_spotify_volume(70)` |
| *"Play [song] by [artist]"* | `play_track(query)` |

---

## Functions

```python
play() -> str
pause() -> str
next_track() -> str
previous_track() -> str
get_current_track() -> str          # "Song Name by Artist"
set_spotify_volume(level: int)      # 0–100, Spotify internal volume
play_track(query: str) -> str       # Search and play
```

---

## play_track — Two Modes

**Without `SPOTIFY_TOKEN`** (default):
- Opens `spotify:search:{query}` URI — Spotify opens and shows search results, but doesn't auto-play

**With `SPOTIFY_TOKEN`** in `.env`:
- Calls Spotify Web API `/v1/search` → gets track URI → plays directly via AppleScript

To get a token: create an app at [developer.spotify.com](https://developer.spotify.com), get a client credentials token, add to `.env`:
```
SPOTIFY_TOKEN=your_token_here
```

---

## Implementation Notes

- All playback controls use `tell application "Spotify" to {action}`
- Spotify must be open; if not, `play()` will launch it automatically via AppleScript
- `set_spotify_volume` sets Spotify's internal volume (independent of system volume)

---

## See Also

- [[MacControl]] — system-level volume via `set_volume()`
- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
