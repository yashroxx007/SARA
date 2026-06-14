# SARA — Feature QA Checklist

> Run this end-to-end after a fresh launch. Say each line out loud, mark the result.
> **Restart SARA before starting** so the latest code is loaded.

Legend: ✅ pass · ❌ fail · ⚠️ partial. Note the actual spoken reply when it's wrong.

---

## Pre-flight

| Check | Expected | Result | Notes |
|---|---|---|---|
| MLX server up | `curl -s localhost:8080/v1/models` returns JSON | | |
| Boot is clean | No `pkg_resources` warning; `[LLM] server reachable` printed | | |
| Greeting | SARA says "Hey Boss, I'm online." | | |

## Red flags to watch on EVERY reply
_(these are the bugs we've been killing — catch regressions)_

- [ ] **Fake success** — claims it did something but no `[TOOL] …` line printed
- [ ] **Param/code leak** — says tool names, "forecast_days", backticks, code
- [ ] **Sign-off filler** — "Is there anything else?", "Let me know if…"
- [ ] **Double-announce** — "I'll do X… X is done" in one reply
- [ ] **Doesn't call you "Boss"**
- [ ] **Asks instead of acting** on a clear request

---

## Wake word + conversation flow

| Say | Expected | Result | Notes |
|---|---|---|---|
| "Hey SARA" | Wakes, `[AWAKE]` in log | | |
| (follow-up without wake word) | Responds, no re-wake needed | | |
| Stay silent ~3s | Goes back to sleep | | |
| "Hey SARA" … "that's all" | Acknowledges, sleeps | | |

## Tools (watch for the `[TOOL] <name>` log line each time)

| Say | Expected | `[TOOL]` fired? | Result | Notes |
|---|---|---|---|---|
| "What's the weather?" | Current conditions, your city | get_weather | | |
| "Is it going to rain tomorrow?" | Tomorrow's forecast + rain % | get_weather | | |
| "What time is it?" | Current time | get_current_datetime | | |
| "Take a note: add dark mode to Arisn" | Confirms; **check Notes app** | create_note | | |
| "Remind me to call the bank tomorrow at 11am" | Confirms; **check Reminders** (correct date/time) | create_reminder | | |
| "What's on my calendar today?" | Reads today's events | calendar | | |
| "Add an event tomorrow 2 to 3pm called Review" | Confirms; **check Calendar** | calendar | | |
| "How's the Mac doing?" | CPU / RAM / battery | system_stats | | |
| "What's eating my CPU?" | Real top processes (not all 0%) | system_stats | | |
| "How much storage is left?" | Disk usage | system_stats | | |
| "Open Spotify" | Spotify actually opens | spotify | | |
| "Play / pause / skip" | Playback changes | spotify | | |
| "Play Enemy by Imagine Dragons" | Opens search (honest: can't auto-play w/o token) | spotify | | |
| "Set volume to 30" | Volume changes | mac_control | | |
| "Open Safari" / "Quit Safari" | App opens / quits | mac_control | | |
| "Set a 1-minute timer" | Fires after 1 min, speaks "done, Boss" | timer | | |
| "Find my resume" | Lists matching files | file_manager | | |
| "What's on my Desktop?" | Lists Desktop items | file_manager | | |
| "Who's the CEO of OpenAI?" | Web answer | web_search | | |
| "What's on my screen?" | Describes screen (routes to Claude) | screen_context | | |
| "What's the status on Arisn?" | Pulls live STATUS.md + vault | projects | | |
| "Log to Arisn: <something>" | Confirms; **check projects/arisn-app.md** | projects | | |
| "Text <name> that I'll be late" | **Confirms before sending**, then sends | messaging | | |

## Multi-step chaining

| Say | Expected | Result | Notes |
|---|---|---|---|
| "Remind me to call the bank tomorrow at 11am" | datetime → reminder, no "what time is it?" question, no crash | | |

## Persona

| Say | Expected | Result | Notes |
|---|---|---|---|
| "Should I launch this month or wait?" | Direct opinion, not a list of considerations | | |
| "I've been putting off the deck for 3 days" | Calls it out, doesn't sympathize | | |
| Any reply | Terse, "Boss", no markdown, no sign-off | | |

## Memory

| Say | Expected | Result | Notes |
|---|---|---|---|
| Tell SARA a fact, then ask about it later | Recalls it within the session | | |
| Long session (20+ exchanges) | `[MEMORY] Summarised …`; still coherent | | |
| Watch the log | `[MEMORY] Dropped orphaned tool_result` should NOT appear every turn | | |

## Graceful failure

| Do | Expected | Result | Notes |
|---|---|---|---|
| `kill` the MLX server, then speak | "Can't reach the local model, Boss" — no crash | | |
| Ask for a tool that errors | Reports the failure honestly — no fake success, no crash | | |

---

## Bugs found

| # | Feature | What you said | What SARA did | Severity |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
