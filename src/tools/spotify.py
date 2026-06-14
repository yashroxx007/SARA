import time
import subprocess


def _osa(script: str):
    """Run an AppleScript line against Spotify. Returns (ok, output_or_error)."""
    full = f'tell application "Spotify" to {script}'
    r = subprocess.run(["osascript", "-e", full], capture_output=True, text=True)
    if r.returncode != 0:
        return False, r.stderr.strip()
    return True, r.stdout.strip()


def _is_running() -> bool:
    r = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to (name of processes) contains "Spotify"'],
        capture_output=True, text=True,
    )
    return r.stdout.strip() == "true"


def _ensure_running() -> bool:
    """Launch + activate Spotify if it isn't already up. Returns True if running."""
    if _is_running():
        return True
    launch = subprocess.run(["open", "-a", "Spotify"], capture_output=True, text=True)
    if launch.returncode != 0:
        return False
    # Wait for the app to register (cold launch can take a couple seconds)
    for _ in range(20):
        if _is_running():
            time.sleep(0.5)  # let AppleScript become responsive
            return True
        time.sleep(0.25)
    return False


def open_spotify() -> str:
    if _ensure_running():
        subprocess.run(["osascript", "-e", 'tell application "Spotify" to activate'], capture_output=True)
        return "Spotify is open."
    return "Couldn't open Spotify, Boss — is it installed?"


def play() -> str:
    if not _ensure_running():
        return "Couldn't open Spotify, Boss."
    ok, err = _osa("play")
    if not ok:
        return f"Couldn't start playback: {err}"
    state_ok, state = _osa("get player state")
    if state_ok and state == "playing":
        name_ok, name = _osa("get name of current track")
        return f"Playing{(' ' + name) if name_ok and name else ''}."
    return "Told Spotify to play, but it doesn't report as playing — there may be no track queued."


def pause() -> str:
    if not _is_running():
        return "Spotify isn't open, Boss."
    ok, err = _osa("pause")
    return "Paused." if ok else f"Couldn't pause: {err}"


def next_track() -> str:
    if not _is_running():
        return "Spotify isn't open, Boss."
    ok, err = _osa("next track")
    if not ok:
        return f"Couldn't skip: {err}"
    return get_current_track()


def previous_track() -> str:
    if not _is_running():
        return "Spotify isn't open, Boss."
    ok, err = _osa("previous track")
    if not ok:
        return f"Couldn't go back: {err}"
    return get_current_track()


def get_current_track() -> str:
    if not _is_running():
        return "Spotify isn't open, Boss."
    name_ok, name = _osa("get name of current track")
    artist_ok, artist = _osa("get artist of current track")
    if not name_ok or not name:
        return "Spotify doesn't seem to be playing anything."
    return f"{name} by {artist}" if artist_ok and artist else name


def set_spotify_volume(level: int) -> str:
    if not _ensure_running():
        return "Couldn't open Spotify, Boss."
    level = max(0, min(100, level))
    ok, err = _osa(f"set sound volume to {level}")
    return f"Spotify volume set to {level}%." if ok else f"Couldn't set volume: {err}"


def play_track(query: str) -> str:
    """Play a track by name. Needs SPOTIFY_TOKEN to resolve name -> track URI;
    without it, we can only open a search (can't auto-play) — and we say so."""
    import urllib.parse, urllib.request, json, os

    if not _ensure_running():
        return "Couldn't open Spotify, Boss."

    token = os.getenv("SPOTIFY_TOKEN")
    if not token:
        subprocess.run(["open", f"spotify:search:{urllib.parse.quote(query)}"], capture_output=True)
        return (f"Opened a Spotify search for '{query}', Boss. I can't auto-play by name "
                f"without a Spotify token — set SPOTIFY_TOKEN to enable that.")

    headers = {"Authorization": f"Bearer {token}"}
    params = urllib.parse.urlencode({"q": query, "type": "track", "limit": "1"})
    req = urllib.request.Request(f"https://api.spotify.com/v1/search?{params}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        items = data["tracks"]["items"]
        if not items:
            return f"No track found for '{query}'."
        uri = items[0]["uri"]
        ok, err = _osa(f'play track "{uri}"')
        if not ok:
            return f"Found it but couldn't play: {err}"
        return f"Playing {items[0]['name']} by {items[0]['artists'][0]['name']}."
    except Exception as e:
        return f"Spotify search error: {e}"
