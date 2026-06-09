import subprocess


def _spotify(script: str) -> str:
    full = f'tell application "Spotify" to {script}'
    result = subprocess.run(["osascript", "-e", full], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Spotify error: {result.stderr.strip()}"
    return result.stdout.strip()


def play() -> str:
    _spotify("play")
    return "Playing."

def pause() -> str:
    _spotify("pause")
    return "Paused."

def next_track() -> str:
    _spotify("next track")
    return "Skipped to next track."

def previous_track() -> str:
    _spotify("previous track")
    return "Back to previous track."

def get_current_track() -> str:
    name = _spotify("get name of current track")
    artist = _spotify("get artist of current track")
    if "error" in name.lower():
        return "Spotify doesn't seem to be playing anything."
    return f"{name} by {artist}"

def set_spotify_volume(level: int) -> str:
    level = max(0, min(100, level))
    _spotify(f"set sound volume to {level}")
    return f"Spotify volume set to {level}%."

def play_track(query: str) -> str:
    """Search and play a track by name via Spotify URI search."""
    import urllib.parse, urllib.request, json, os
    token = os.getenv("SPOTIFY_TOKEN")
    if not token:
        # Fallback: just open Spotify and hope for the best
        subprocess.run(["open", f"spotify:search:{urllib.parse.quote(query)}"])
        return f"Opened Spotify search for '{query}'."
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
        _spotify(f'play track "{uri}"')
        return f"Playing {items[0]['name']} by {items[0]['artists'][0]['name']}."
    except Exception as e:
        return f"Spotify search error: {e}"
