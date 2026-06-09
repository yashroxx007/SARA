# Tool — Screen Context

**Status:** ✅ Live  
**File:** `src/tools/screen_context.py`  
**Added:** v0.5.0

---

## What It Does

Takes a screenshot of the primary display and asks Claude vision to answer a question about it. SARA reads the answer aloud.

---

## Voice Commands

- *"What's on my screen?"*
- *"What does this error say?"*
- *"What am I looking at?"*
- *"Read this article for me"*
- *"What app is open?"*
- *"Summarise what's on screen"*

---

## Function

```python
get_screen_context(question: str = "What is on the screen?") -> str
```

Claude receives the question and the screenshot image, returns 1-3 sentences suitable for speaking aloud.

---

## How It Works

1. `screencapture -x -t png` saves a silent screenshot to a temp file
2. Image is base64-encoded
3. Sent to `claude-sonnet-4-6` as a vision message with the question
4. Response is trimmed for voice — no markdown, no emojis
5. Temp file is deleted immediately after encoding

---

## Implementation Notes

- `-x` flag suppresses the screenshot sound
- Uses `tempfile.NamedTemporaryFile` — cleaned up in a `finally` block
- Model: `claude-sonnet-4-6` (same as SARA's brain — best vision quality)
- `max_tokens=300` — keeps responses concise

---

## Known Limitations

- Captures primary display only on multi-monitor setups
- Slow (~2-3s) due to vision API round trip
- Not suitable for real-time screen monitoring

---

## See Also

- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
