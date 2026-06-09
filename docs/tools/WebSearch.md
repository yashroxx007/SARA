# Tool — Web Search

**Status:** ✅ Live  
**File:** `src/tools/web_search.py`  
**Added:** v0.4.0

---

## What It Does

Real-time web search via DuckDuckGo Instant Answer API. No API key needed. Answers factual questions, looks up people, definitions, and current info.

---

## Voice Commands

- *"Who is [person]?"*
- *"What is [term]?"*
- *"What's the latest on [topic]?"*
- *"Tell me about [company/concept]"*

---

## Function

```python
web_search(query: str) -> str
```

Returns the best available text: abstract first, then related topic snippets, then a "nothing found" message.

---

## API

- **Endpoint:** `https://api.duckduckgo.com/?q={query}&format=json`
- **Auth:** None
- **Timeout:** 6 seconds
- **User-Agent:** `SARAH-assistant/1.0`

---

## Response Priority

1. `AbstractText` — Wikipedia-style summary (best)
2. `RelatedTopics[0..2].Text` — related snippets (fallback)
3. "No instant answer found" message (last resort)

---

## Known Limitations

- Weak on **breaking news** — DuckDuckGo Instant Answers are mostly knowledge-graph facts
- No full web scraping — if you need live news/prices, a Brave Search or SerpAPI key would be needed
- Not good for ambiguous short queries ("apple", "spark")

---

## Planned Upgrade

- Add Brave Search API as a fallback for news/recency-sensitive queries (requires free API key)

---

## See Also

- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
