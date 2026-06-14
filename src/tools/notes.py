import subprocess


def create_note(title, body):
    # Escape backslashes and quotes so titles/bodies with " or \ don't break
    # the AppleScript string (a quote used to silently fail and report success).
    safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
    safe_body = (body or "").replace('\\', '\\\\').replace('"', '\\"')

    script = f'''
    tell application "Notes"
        make new note at folder "Notes" with properties {{name:"{safe_title}", body:"{safe_body}"}}
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't save the note: {result.stderr.strip()}"
    return f"Note '{title}' saved to Notes app."
