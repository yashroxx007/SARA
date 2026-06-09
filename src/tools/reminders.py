import subprocess
from datetime import datetime


def create_reminder(title, notes="", due_date=None):
    safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
    safe_notes = (notes or "").replace('\\', '\\\\').replace('"', '\\"')

    if due_date:
        # Parse Claude's date format and reformat for AppleScript (DD/MM/YYYY locale)
        for fmt in ("%B %d, %Y %H:%M:%S", "%B %d, %Y %H:%M", "%B %d, %Y"):
            try:
                dt = datetime.strptime(due_date.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return f"Couldn't parse date '{due_date}'. Use format like 'June 10, 2026 09:00:00'."

        applescript_date = dt.strftime("%d/%m/%Y %I:%M %p")
        script = f'''tell application "Reminders"
    set newReminder to make new reminder in list "Reminders" with properties {{name:"{safe_title}", body:"{safe_notes}"}}
    set due date of newReminder to date "{applescript_date}"
end tell'''
    else:
        script = f'''tell application "Reminders"
    make new reminder in list "Reminders" with properties {{name:"{safe_title}", body:"{safe_notes}"}}
end tell'''

    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Failed to create reminder: {result.stderr.strip()}"
    return f"Reminder '{title}' created."
