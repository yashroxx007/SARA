import subprocess


# ── Volume ────────────────────────────────────────────────────────────────────

def set_volume(level: int) -> str:
    """level: 0-100"""
    level = max(0, min(100, level))
    subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
    return f"Volume set to {level}%."

def mute() -> str:
    subprocess.run(["osascript", "-e", "set volume with output muted"], check=True)
    return "Muted."

def unmute() -> str:
    subprocess.run(["osascript", "-e", "set volume without output muted"], check=True)
    return "Unmuted."


# ── Brightness ────────────────────────────────────────────────────────────────

def set_brightness(level: int) -> str:
    """level: 0-100"""
    level = max(0, min(100, level))
    value = round(level / 100, 2)
    script = f'tell application "System Events" to set brightness of display 1 to {value}'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        try:
            fb = subprocess.run(["brightness", str(value)], capture_output=True, text=True)
            if fb.returncode != 0:
                return "Couldn't set brightness. Go to System Settings → Privacy → Accessibility and allow SARA, then try again."
        except FileNotFoundError:
            return "Couldn't set brightness. Run 'brew install brightness' to enable this, or grant Accessibility permission in System Settings."
    return f"Brightness set to {level}%."


# ── Apps ──────────────────────────────────────────────────────────────────────

def open_app(app_name: str) -> str:
    result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't open '{app_name}': {result.stderr.strip()}"
    return f"Opening {app_name}."

def quit_app(app_name: str) -> str:
    script = f'tell application "{app_name}" to quit'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't quit '{app_name}': {result.stderr.strip()}"
    return f"Quit {app_name}."


# ── System ────────────────────────────────────────────────────────────────────

def lock_screen() -> str:
    subprocess.run(["osascript", "-e",
        'tell application "System Events" to keystroke "q" using {control down, command down}'],
        capture_output=True)
    return "Locking screen."

def empty_trash() -> str:
    script = 'tell application "Finder" to empty trash'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't empty trash: {result.stderr.strip()}"
    return "Trash emptied."
