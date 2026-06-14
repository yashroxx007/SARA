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


def get_events_in_next_minutes(minutes: int = 20) -> list[dict]:
    """Returns events starting within the next `minutes` from now. Used by proactive mode."""
    seconds = minutes * 60
    script = f'''
    tell application "Calendar"
        set now to current date
        set cutoff to now + {seconds}
        set found to {{}}
        repeat with cal in calendars
            set calEvents to (every event of cal whose start date >= now and start date <= cutoff)
            repeat with e in calEvents
                set end of found to (summary of e) & "|" & ((start date of e) as string)
            end repeat
        end repeat
        return found as string
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    raw = result.stdout.strip()
    events = []
    for item in raw.split(", "):
        if "|" in item:
            parts = item.split("|", 1)
            events.append({"title": parts[0].strip(), "start": parts[1].strip()})
    return events


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

    # Escape so titles/calendar names with " or \ don't break the AppleScript
    safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
    safe_calendar = calendar.replace('\\', '\\\\').replace('"', '\\"')

    script = f'''
    tell application "Calendar"
        tell calendar "{safe_calendar}"
            make new event with properties {{summary:"{safe_title}", start date:date "{as_start}", end date:date "{as_end}"}}
        end tell
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't create event: {result.stderr.strip()}"
    return f"Event '{title}' created on {start_dt.strftime('%-d %B at %I:%M %p')}."
