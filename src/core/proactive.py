"""
Proactive mode — background thread that monitors time and calendar,
speaking unprompted when something is worth saying.
"""

import threading
import time
from datetime import datetime


_speak_fn = None
_client = None
_system_prompt = None
_running = False


def init(speak_fn, client, system_prompt):
    global _speak_fn, _client, _system_prompt
    _speak_fn = speak_fn
    _client = client
    _system_prompt = system_prompt


def _check_and_speak():
    """Called every minute. Decides if SARA should say something."""
    now = datetime.now()
    hour, minute = now.hour, now.minute

    # Morning briefing at 8:00 AM
    if hour == 8 and minute == 0:
        _deliver_briefing("morning")
        return

    # Evening wrap at 6:00 PM
    if hour == 18 and minute == 0:
        _deliver_briefing("evening")
        return

    # Meeting alerts — 15 min before any calendar event
    _check_upcoming_meetings(now)


def _deliver_briefing(period: str):
    try:
        from src.tools.calendar_tool import get_todays_events
        from src.tools.weather import get_weather

        events = get_todays_events()
        weather = get_weather("Bangalore")

        if period == "morning":
            prompt = f"""It's 8am. Give Yash a sharp morning briefing — 2-3 sentences max, spoken aloud.
Include: today's weather ({weather}) and his schedule ({events}).
If nothing's scheduled, note that too. Be direct. No markdown, no emojis."""
        else:
            prompt = f"""It's 6pm. Give Yash a quick end-of-day check-in — 1-2 sentences.
Today's events were: {events}.
Reference what he had today. Maybe push him to wind down or note anything pending. Direct, not preachy."""

        response = _client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=_system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        _speak_fn(response.content[0].text.strip())
    except Exception as e:
        print(f"[PROACTIVE] Briefing error: {e}")


def _check_upcoming_meetings(now: datetime):
    try:
        from src.tools.calendar_tool import get_events_in_next_minutes

        # Only look at events starting in the next 16 minutes from right now
        events = get_events_in_next_minutes(minutes=16)
        if not events:
            return

        for event in events:
            _speak_fn(f"Heads up Boss, {event['title']} starts in about 15 minutes.")
    except Exception as e:
        print(f"[PROACTIVE] Meeting check error: {e}")


def _loop():
    global _running
    # Sleep to the next minute boundary FIRST — don't fire immediately on boot
    now = datetime.now()
    time.sleep(60 - now.second)
    while _running:
        try:
            _check_and_speak()
        except Exception as e:
            print(f"[PROACTIVE] Loop error: {e}")
        now = datetime.now()
        time.sleep(60 - now.second)


def start():
    global _running
    if _running:
        return
    _running = True
    t = threading.Thread(target=_loop, daemon=True, name="ProactiveThread")
    t.start()
    print("[PROACTIVE] Mode active — morning briefing at 8am, meeting alerts enabled.")


def stop():
    global _running
    _running = False
