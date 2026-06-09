import subprocess

def create_note(title, body):
    script = f'''
    tell application "Notes"
        make new note at folder "Notes" with properties {{name:"{title}", body:"{body}"}}
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
    return f"Note '{title}' saved to Notes app."