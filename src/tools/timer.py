import threading


# Will be injected from main.py so the timer can call speak()
_speak_fn = None

def set_speak(fn):
    global _speak_fn
    _speak_fn = fn


def set_timer(minutes: float, label: str = "Timer") -> str:
    seconds = minutes * 60

    def _fire():
        import time
        time.sleep(seconds)
        msg = f"{label} done. {int(minutes)} {'minute' if minutes == 1 else 'minutes'} are up."
        print(f"\n[TIMER] {msg}")
        if _speak_fn:
            _speak_fn(msg)

    t = threading.Thread(target=_fire, daemon=True)
    t.start()

    mins = int(minutes)
    secs = int((minutes % 1) * 60)
    if secs:
        duration = f"{mins}m {secs}s"
    else:
        duration = f"{mins} minute{'s' if mins != 1 else ''}"
    return f"{label} set for {duration}. I'll let you know."
