from datetime import datetime


def get_current_datetime():
    now = datetime.now()
    return now.strftime("%-d %B %Y, %I:%M %p")  # e.g. "9 June 2026, 08:04 PM"
