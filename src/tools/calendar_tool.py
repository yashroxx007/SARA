import subprocess
from datetime import datetime


def get_todays_events() -> str:
    script = '''
    tell application "Calendar"
        set today to current date
        set startOfDay to today - (time of today)
        set endOfDay to startOfDay + 86399
        set allEvents to {}
        repeat with cal in calendars
            set calEvents to (every event of cal whose start date >= startOfDay and start date <= endOfDay)
            repeat with e in calEvents
                set end of allEvents to (summary of e) & " at " & ((start date of e) as string)
            end repeat
        end repeat
        if length of allEvents is 0 then
            return "No events today."
        end if
        return allEvents as string
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Calendar error: {result.stderr.strip()}"
    return result.stdout.strip()


def get_upcoming_events(days: int = 7) -> str:
    script = f'''
    tell application "Calendar"
        set today to current date
        set startOfDay to today - (time of today)
        set endDate to startOfDay + ({days} * 86400)
        set allEvents to {{}}
        repeat with cal in calendars
            set calEvents to (every event of cal whose start date >= startOfDay and start date <= endDate)
            repeat with e in calEvents
                set end of allEvents to (summary of e) & " — " & ((start date of e) as string)
            end repeat
        end repeat
        if length of allEvents is 0 then
            return "No upcoming events in the next {days} days."
        end if
        return allEvents as string
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Calendar error: {result.stderr.strip()}"
    return result.stdout.strip()


def create_event(title: str, start: str, end: str, calendar: str = "Home") -> str:
    """
    start / end: 'Month DD, YYYY HH:MM:SS' e.g. 'June 10, 2026 14:00:00'
    """
    for fmt in ("%B %d, %Y %H:%M:%S", "%B %d, %Y %H:%M", "%B %d, %Y"):
        try:
            start_dt = datetime.strptime(start.strip(), fmt)
            end_dt = datetime.strptime(end.strip(), fmt)
            break
        except ValueError:
            continue
    else:
        return f"Couldn't parse dates. Use format like 'June 10, 2026 14:00:00'."

    as_start = start_dt.strftime("%d/%m/%Y %I:%M %p")
    as_end = end_dt.strftime("%d/%m/%Y %I:%M %p")

    script = f'''
    tell application "Calendar"
        tell calendar "{calendar}"
            make new event with properties {{summary:"{title}", start date:date "{as_start}", end date:date "{as_end}"}}
        end tell
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't create event: {result.stderr.strip()}"
    return f"Event '{title}' created on {start_dt.strftime('%-d %B at %I:%M %p')}."
