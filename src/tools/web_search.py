import urllib.request
import urllib.parse
import json


def web_search(query: str) -> str:
    """Search the web via DuckDuckGo Instant Answer API (no key needed)."""
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    })
    url = f"https://api.duckduckgo.com/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SARAH-assistant/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())

        # Best instant answer
        if data.get("AbstractText"):
            return data["AbstractText"]

        # Related topics fallback
        topics = data.get("RelatedTopics", [])
        snippets = []
        for t in topics[:3]:
            if isinstance(t, dict) and t.get("Text"):
                snippets.append(t["Text"])
        if snippets:
            return " | ".join(snippets)

        return f"No instant answer found for '{query}'. Try rephrasing."
    except Exception as e:
        return f"Search failed: {e}"
