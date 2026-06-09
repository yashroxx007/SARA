# Tool — Weather

**Status:** ✅ Live  
**File:** `src/tools/weather.py`  
**Added:** v0.2.0

---

## What It Does

Fetches current weather conditions for a city using the `wttr.in` API. No API key required.

---

## Voice Commands

- *"What's the weather?"*
- *"Weather in Mumbai"*
- *"Is it going to rain today?"*

---

## Function

```python
get_weather(city: str = "Bangalore") -> str
```

Returns a string like: `"Bangalore: Partly cloudy, 28°C"`

---

## API

- **Endpoint:** `https://wttr.in/{city}?format=3`
- **Auth:** None
- **Fallback:** Returns error string on failure

---

## Known Limitations

- Instant conditions only — no forecast
- Accuracy depends on wttr.in uptime

---

## See Also

- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
