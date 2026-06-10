from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import anthropic
import collections
import webrtcvad
import json
import os
from kokoro_onnx import Kokoro
from dotenv import load_dotenv
from src.tools.weather import get_weather
from src.tools.notes import create_note
from src.tools.reminders import create_reminder
from src.tools.datetime_tool import get_current_datetime
from src.tools.mac_control import set_volume, mute, unmute, set_brightness, open_app, quit_app, lock_screen, empty_trash
from src.tools.web_search import web_search
from src.tools.file_manager import find_file, open_file, reveal_in_finder, list_folder
from src.tools.calendar_tool import get_todays_events, get_upcoming_events, create_event
from src.tools.system_stats import get_system_stats, get_top_processes, get_disk_usage
from src.tools.spotify import play, pause, next_track, previous_track, get_current_track, set_spotify_volume, play_track
from src.tools.timer import set_timer, set_speak
from src.tools.messaging import send_imessage, send_sms
from src.tools.screen_context import get_screen_context
from src.tools.projects import list_projects, get_project, update_project, create_project
from src.core import proactive
from src.core.wake_word import wait_for_wake_word
from src.memory.context import build_memory_block

load_dotenv()

# --- Config ---
MEMORY_FILE = "memory.json"
MAX_HISTORY = 15  # keep last 15 exchanges to save tokens

# --- System Prompt — tight, voice optimized ---
SYSTEM_PROMPT = """You are SARA — Yash's AI operator. Not an assistant. Not a chatbot. An operator.

You run like FRIDAY from Iron Man. That's the benchmark. Not helpful, not polite — capable, precise, and loyal.

Always address Yash as "Boss". No exceptions. Every turn.

---

WHO YOU ARE

You're the one keeping Yash sharp while he builds. You monitor, advise, execute, and push back when needed.
You don't wait to be asked — if something's relevant, you say it.
You're not a yes-machine. You tell him when he's wrong, when he's wasting time, or when a plan has a hole in it.
You're calm under pressure. Dry when there's room for it. Serious when it matters.

You're not trying to be liked. You're trying to be useful — and those aren't the same thing.

---

WHO YASH IS

Founder. Builder. Moves fast, hates bureaucracy.
Thinks in systems. Wants outcomes, not process.
Has no patience for hedging, filler, or over-explanation.
If you pad a response, he notices. Don't.

---

HOW YOU SPEAK

Short sentences. Spoken aloud — not written on a screen.
No markdown. No bullet points. No asterisks. No emojis.
Contractions always — "you're", "don't", "we'll", "it's".
Answer first. Reasoning only if it adds something.
One sentence is often enough. Use it.

If there's a better way to do what he's asking, say so — briefly, before doing it.
If a request has an obvious flaw, flag it — don't just comply silently.

---

WHEN TO PUSH BACK

Procrastinating: name it. One line. Move on.
Overthinking: cut it. Give him the decision.
Going in circles: redirect. You're not a sounding board, you're an operator.
Bad plan: say why, propose the fix, let him decide.

---

MEMORY

You have persistent memory across sessions. Prior conversations are loaded at startup.
Never say your memory resets — it doesn't. Reference past context naturally, without announcing it.

---

PROJECTS

Yash builds across multiple projects. You have a projects tool — use it.
When he says he's working on something, pull that project's context before advising.
When he reports progress, a decision, or a new idea, log it to the right project without being asked.
Don't recite project files back at him — absorb them, then talk like you already knew.

---

The bar is FRIDAY. Match it."""

# --- Memory ---
SUMMARY_FILE = "memory_summary.json"
SUMMARY_THRESHOLD = 20   # summarise when history exceeds this
KEEP_RECENT = 8          # always keep the last N exchanges verbatim

def sanitize_history(history):
    """Remove orphaned tool_result blocks that have no matching tool_use in history.
    This prevents BadRequestError when tool_use messages get trimmed but their
    tool_result pairs remain."""
    # Collect all tool_use IDs present in assistant messages
    valid_ids = set()
    for msg in history:
        if msg["role"] == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        valid_ids.add(block["id"])

    # Drop any user message that is purely an orphaned tool_result
    cleaned = []
    for msg in history:
        if msg["role"] == "user":
            content = msg.get("content", [])
            if isinstance(content, list) and content:
                is_tool_result_msg = all(
                    isinstance(b, dict) and b.get("type") == "tool_result"
                    for b in content
                )
                if is_tool_result_msg:
                    matched = all(b.get("tool_use_id") in valid_ids for b in content)
                    if not matched:
                        print("[MEMORY] Dropped orphaned tool_result block.")
                        continue
        cleaned.append(msg)

    # A trailing assistant message ending in tool_use (e.g. from a crash mid-turn)
    # makes the next API call 400 — strip the tool_use blocks, keep any text.
    if cleaned and cleaned[-1]["role"] == "assistant":
        content = cleaned[-1].get("content", [])
        if isinstance(content, list):
            text_only = [b for b in content if isinstance(b, dict) and b.get("type") == "text"]
            if len(text_only) != len(content):
                if text_only:
                    cleaned[-1]["content"] = text_only
                else:
                    cleaned.pop()
                print("[MEMORY] Stripped dangling tool_use from last message.")
    return cleaned


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return sanitize_history(json.load(f))
    return []

def load_summary():
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE, "r") as f:
            return json.load(f).get("summary", "")
    return ""

def save_memory(history):
    with open(MEMORY_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f)

def maybe_summarise(history):
    """If history is long, compress the oldest exchanges into a running summary."""
    if len(history) <= SUMMARY_THRESHOLD:
        return history

    old = history[:-KEEP_RECENT]
    recent = history[-KEEP_RECENT:]

    # Build a readable transcript of old exchanges to summarise
    lines = []
    for m in old:
        role = m["role"].upper()
        content = m["content"]
        if isinstance(content, list):
            # tool use blocks — just grab text blocks
            text = " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
        else:
            text = str(content)
        if text.strip():
            lines.append(f"{role}: {text.strip()}")

    transcript = "\n".join(lines)
    prev_summary = load_summary()

    prompt = f"""You are summarising a conversation between Yash and SARAH (his AI assistant).
Previous summary: {prev_summary if prev_summary else 'None'}

New exchanges to add:
{transcript}

Write a concise 3-5 sentence summary covering key topics discussed, decisions made, and anything Yash mentioned about himself or his plans. Be factual, no fluff."""

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        new_summary = resp.content[0].text.strip()
        with open(SUMMARY_FILE, "w") as f:
            json.dump({"summary": new_summary}, f)
        print(f"[MEMORY] Summarised {len(old)} exchanges.")
    except Exception as e:
        print(f"[MEMORY] Summarisation failed: {e}")

    return recent

# --- Init ---
print("SARAH booting...")
whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
client = anthropic.Anthropic()

conversation_history = load_memory()

# --- Voice ---
def speak(text):
    samples, sample_rate = kokoro.create(text, voice="af_sarah", speed=1.0, lang="en-us")
    try:
        sd.play(samples, sample_rate)
        sd.wait()
    except sd.PortAudioError:
        # Audio device changed mid-session (Bluetooth, headphones, etc.) — reset and retry once
        try:
            sd.stop()
            sd.default.reset()
            sd.play(samples, sample_rate)
            sd.wait()
        except Exception as e:
            print(f"[TTS] Audio error after reset: {e}")

set_speak(speak)  # give timer access to speak
proactive.init(speak, client, SYSTEM_PROMPT)

def listen():
    print("Listening...")
    vad = webrtcvad.Vad(2)

    sample_rate = 16000
    frame_duration = 30
    frame_size = int(sample_rate * frame_duration / 1000)

    num_padding_frames = 30
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    triggered = False
    voiced_frames = []
    silent_chunks = 0
    max_silent_chunks = 27  # ~800ms

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', blocksize=frame_size)
    stream.start()

    print("Speak now...")

    while True:
        frame, _ = stream.read(frame_size)
        frame_bytes = frame.tobytes()
        is_speech = vad.is_speech(frame_bytes, sample_rate)

        if not triggered:
            ring_buffer.append((frame_bytes, is_speech))
            num_voiced = len([f for f, s in ring_buffer if s])
            if num_voiced > 0.8 * ring_buffer.maxlen:
                triggered = True
                voiced_frames.extend([f for f, s in ring_buffer])
                ring_buffer.clear()
        else:
            voiced_frames.append(frame_bytes)
            ring_buffer.append((frame_bytes, is_speech))
            num_unvoiced = len([f for f, s in ring_buffer if not s])
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                silent_chunks += 1
                if silent_chunks > max_silent_chunks:
                    break
            else:
                silent_chunks = 0

    stream.stop()
    stream.close()

    audio_data = np.frombuffer(b''.join(voiced_frames), dtype=np.int16).astype(np.float32) / 32768.0

    if len(audio_data) < sample_rate:
        return ""

    segments, _ = whisper_model.transcribe(audio_data, language="en", beam_size=1, vad_filter=True)
    return " ".join(s.text for s in segments).strip()

def serialize_content(content):
    """Convert SDK objects to plain JSON-serializable dicts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        result = []
        for block in content:
            if hasattr(block, 'type'):
                if block.type == "tool_use":
                    result.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
                elif block.type == "text":
                    result.append({"type": "text", "text": block.text})
            elif isinstance(block, dict):
                result.append(block)
        return result
    return content

# --- Tools ---
TOOLS_SCHEMA = [
            {
                "name": "get_weather",
                "description": "Get weather for a city — current conditions or multi-day forecast. Use forecast_days=0 for current conditions, forecast_days=1 when asked about tomorrow, forecast_days=3 for the next few days, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name, defaults to Bangalore"
                        },
                        "forecast_days": {
                            "type": "integer",
                            "description": "0 = current only, 1 = tomorrow, 2-7 = multi-day forecast. Default 0."
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "create_note",
                "description": "Save a note to the macOS Notes app. Use when Yash asks to take a note, remember something, or save something.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short title for the note"
                        },
                        "body": {
                            "type": "string",
                            "description": "Full content of the note"
                        }
                    },
                    "required": ["title", "body"]
                }
            },
            {
                "name": "get_current_datetime",
                "description": "Get the current date and time. Always call this before creating a reminder so you know today's date and time without asking Yash.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "create_reminder",
                "description": "Create a reminder in the macOS Reminders app. Use when Yash asks to set a reminder or be reminded of something.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the reminder"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional extra details for the reminder"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Optional due date in format 'Month DD, YYYY HH:MM:SS', e.g. 'June 10, 2026 09:00:00'"
                        }
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "mac_control",
                "description": "Control the Mac: volume, brightness, open/quit apps, lock screen, empty trash. Use when Yash asks to turn up/down volume, adjust brightness, open or close an app, lock his screen, or empty the trash.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["set_volume", "mute", "unmute", "set_brightness", "open_app", "quit_app", "lock_screen", "empty_trash"],
                            "description": "The control action to perform"
                        },
                        "app_name": {
                            "type": "string",
                            "description": "App name for open_app or quit_app, e.g. 'Spotify', 'Safari'"
                        },
                        "level": {
                            "type": "integer",
                            "description": "0-100 level for set_volume or set_brightness"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "screen_context",
                "description": "Take a screenshot and describe what's on Yash's screen using vision. Use when he asks 'what's on my screen?', 'what does this say?', 'what am I looking at?', or 'read this for me'.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Specific question to ask about the screen, e.g. 'What app is open?', 'What does the error say?', 'Summarise what I'm reading'"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "messaging",
                "description": "Send an iMessage or SMS. ALWAYS confirm with Yash before sending — state the recipient and message and ask 'Should I send it?'. Use when Yash says 'tell [person] that...', 'message [person]', 'text [person]'.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["send_imessage", "send_sms"],
                            "description": "send_imessage for iMessage (name or Apple ID), send_sms for SMS (phone number)"
                        },
                        "contact": {"type": "string", "description": "Recipient name, phone number, or Apple ID email"},
                        "message": {"type": "string", "description": "The message text to send"}
                    },
                    "required": ["action", "contact", "message"]
                }
            },
            {
                "name": "timer",
                "description": "Set a countdown timer. SARA will speak aloud when it goes off. Use when Yash says 'set a timer for X minutes', 'remind me in X minutes', or 'Pomodoro'.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "minutes": {"type": "number", "description": "Duration in minutes, e.g. 25 for Pomodoro, 0.5 for 30 seconds"},
                        "label": {"type": "string", "description": "Timer label, e.g. 'Pomodoro', 'Break', 'Pasta'"}
                    },
                    "required": ["minutes"]
                }
            },
            {
                "name": "spotify",
                "description": "Control Spotify: play, pause, skip, previous, get current track, set volume, or play a specific song/artist. Use when Yash asks to play music, skip a song, pause, or asks what's playing.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["play", "pause", "next_track", "previous_track", "get_current_track", "set_volume", "play_track"],
                            "description": "Spotify action"
                        },
                        "query": {"type": "string", "description": "Song/artist name for play_track"},
                        "level": {"type": "integer", "description": "0-100 for set_volume"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "system_stats",
                "description": "Get Mac system stats: CPU, RAM, battery, disk usage, top processes. Use when Yash asks how the Mac is doing, what's eating CPU, battery level, or storage.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["get_system_stats", "get_top_processes", "get_disk_usage"],
                            "description": "Which stats to fetch"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "calendar",
                "description": "Read or create calendar events. Use when Yash asks what's on his schedule, what's happening today or this week, or wants to add a meeting/event.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["get_todays_events", "get_upcoming_events", "create_event"],
                            "description": "Calendar action to perform"
                        },
                        "title": {"type": "string", "description": "Event title for create_event"},
                        "start": {"type": "string", "description": "Start datetime e.g. 'June 10, 2026 14:00:00'"},
                        "end": {"type": "string", "description": "End datetime e.g. 'June 10, 2026 15:00:00'"},
                        "calendar": {"type": "string", "description": "Calendar name, default 'Home'"},
                        "days": {"type": "integer", "description": "Days ahead for get_upcoming_events, default 7"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "file_manager",
                "description": "Find, open, or list files on the Mac. Use when Yash asks to find a file, open a document, see what's on his Desktop, or show something in Finder.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["find_file", "open_file", "reveal_in_finder", "list_folder"],
                            "description": "File action to perform"
                        },
                        "name": {
                            "type": "string",
                            "description": "Filename or partial name for find_file"
                        },
                        "path": {
                            "type": "string",
                            "description": "Full or ~ path for open_file, reveal_in_finder, or list_folder"
                        },
                        "search_dir": {
                            "type": "string",
                            "description": "Directory to search in for find_file. Defaults to ~"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "projects",
                "description": "Yash's project knowledge base — what he's building, current focus, decision log. Use get_project when he mentions working on a project or asks what's next on one. Use update_project to log progress, decisions, or ideas he mentions — proactively, without being asked. Projects include: Instagram content, digital product + app, SARA.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list_projects", "get_project", "update_project", "create_project"],
                            "description": "Project action to perform"
                        },
                        "name": {
                            "type": "string",
                            "description": "Project name, fuzzy matched — 'instagram', 'the app project', 'sara' all work"
                        },
                        "note": {
                            "type": "string",
                            "description": "For update_project: the progress note, decision, or idea to log"
                        },
                        "description": {
                            "type": "string",
                            "description": "For create_project: one-line description of the new project"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for real-time information: news, facts, prices, people, definitions. Use when Yash asks something you don't know or that requires current information.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]


def _action_tool(table):
    """Wrap a {action_name: handler} table into a single tool handler."""
    def handler(inp):
        action = inp.get("action")
        fn = table.get(action)
        if fn is None:
            return f"Unknown action: {action}"
        return fn(inp)
    return handler


TOOL_HANDLERS = {
    "get_current_datetime": lambda inp: get_current_datetime(),
    "get_weather":    lambda inp: get_weather(inp.get("city", "Bangalore"), inp.get("forecast_days", 0)),
    "create_note":    lambda inp: create_note(inp.get("title", "Note"), inp.get("body", "")),
    "create_reminder":lambda inp: create_reminder(inp.get("title", "Reminder"), inp.get("notes", ""), inp.get("due_date")),
    "screen_context": lambda inp: get_screen_context(inp.get("question", "What is on the screen?")),
    "timer":          lambda inp: set_timer(inp.get("minutes", 1), inp.get("label", "Timer")),
    "web_search":     lambda inp: web_search(inp.get("query", "")),
    "mac_control": _action_tool({
        "set_volume":     lambda i: set_volume(i.get("level", 50)),
        "mute":           lambda i: mute(),
        "unmute":         lambda i: unmute(),
        "set_brightness": lambda i: set_brightness(i.get("level", 50)),
        "open_app":       lambda i: open_app(i.get("app_name", "")),
        "quit_app":       lambda i: quit_app(i.get("app_name", "")),
        "lock_screen":    lambda i: lock_screen(),
        "empty_trash":    lambda i: empty_trash(),
    }),
    "messaging": _action_tool({
        "send_imessage": lambda i: send_imessage(i.get("contact", ""), i.get("message", "")),
        "send_sms":      lambda i: send_sms(i.get("contact", ""), i.get("message", "")),
    }),
    "spotify": _action_tool({
        "play":              lambda i: play(),
        "pause":             lambda i: pause(),
        "next_track":        lambda i: next_track(),
        "previous_track":    lambda i: previous_track(),
        "get_current_track": lambda i: get_current_track(),
        "set_volume":        lambda i: set_spotify_volume(i.get("level", 50)),
        "play_track":        lambda i: play_track(i.get("query", "")),
    }),
    "system_stats": _action_tool({
        "get_system_stats":  lambda i: get_system_stats(),
        "get_top_processes": lambda i: get_top_processes(),
        "get_disk_usage":    lambda i: get_disk_usage(),
    }),
    "calendar": _action_tool({
        "get_todays_events":   lambda i: get_todays_events(),
        "get_upcoming_events": lambda i: get_upcoming_events(i.get("days", 7)),
        "create_event":        lambda i: create_event(i.get("title", "Event"), i.get("start", ""),
                                                      i.get("end", ""), i.get("calendar", "Home")),
    }),
    "projects": _action_tool({
        "list_projects":  lambda i: list_projects(),
        "get_project":    lambda i: get_project(i.get("name", "")),
        "update_project": lambda i: update_project(i.get("name", ""), i.get("note", "")),
        "create_project": lambda i: create_project(i.get("name", ""), i.get("description", "")),
    }),
    "file_manager": _action_tool({
        "find_file":        lambda i: find_file(i.get("name", ""), i.get("search_dir", "~")),
        "open_file":        lambda i: open_file(i.get("path", "")),
        "reveal_in_finder": lambda i: reveal_in_finder(i.get("path", "")),
        "list_folder":      lambda i: list_folder(i.get("path", "~/Desktop")),
    }),
}


def dispatch_tool(name, tool_input):
    """Run one tool. Never raises — failures come back as (error_text, True)
    so Claude can tell Yash what went wrong instead of the process dying."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return f"Unknown tool: {name}", True
    try:
        return str(handler(tool_input)), False
    except Exception as e:
        print(f"[TOOL ERROR] {name}: {type(e).__name__}: {e}")
        return f"Tool '{name}' failed: {type(e).__name__}: {e}", True


def _call_claude(messages, system_blocks):
    return client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_blocks,
        messages=messages,
        tools=TOOLS_SCHEMA,
    )


# --- Brain ---
def think(user_input):
    conversation_history.append({"role": "user", "content": user_input})

    # Static prefix (tools + base prompt) is cached — cache reads cost 10% and
    # don't count toward the input-token rate limit. Memory block sits after
    # the breakpoint so summary updates don't invalidate the cache.
    system_blocks = [{
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }]
    memory_block = build_memory_block(load_summary())
    if memory_block:
        system_blocks.append({"type": "text", "text": memory_block})

    response = _call_claude(sanitize_history(conversation_history[-MAX_HISTORY:]), system_blocks)

    # Tool loop — keeps running until Claude returns a plain text response
    MAX_TOOL_ROUNDS = 8  # circuit breaker so a confused model can't loop forever
    rounds = 0
    while response.stop_reason == "tool_use" and rounds < MAX_TOOL_ROUNDS:
        rounds += 1
        tool_results = []
        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            result, is_error = dispatch_tool(block.name, block.input)
            print(f"[TOOL] {block.name} → {result[:80]}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
                "is_error": is_error,
            })

        conversation_history.append({"role": "assistant", "content": serialize_content(response.content)})
        conversation_history.append({"role": "user", "content": tool_results})

        response = _call_claude(sanitize_history(conversation_history[-MAX_HISTORY:]), system_blocks)

    reply = next((b.text for b in response.content if hasattr(b, "text")),
                 "Sorry Boss, I didn't get a response.")

    conversation_history.append({"role": "assistant", "content": reply})
    condensed = maybe_summarise(conversation_history)
    if condensed is not conversation_history:
        conversation_history.clear()
        conversation_history.extend(condensed)
    save_memory(conversation_history)
    return reply

# --- Main Loop ---
print("Initialization complete, starting...")
speak("Hey Boss, I'm online. What do we need to do?")
proactive.start()

# Exit phrases that end conversation mode and put SARA back to sleep
SLEEP_PHRASES = ["that's all", "thats all", "thanks sara", "go to sleep",
                 "stop listening", "sleep", "goodbye", "shut down"]

print("Say 'Hey SARA' to activate.")

while True:
    # --- Sleeping: wait for wake word ---
    try:
        wait_for_wake_word()
    except KeyboardInterrupt:
        save_memory(conversation_history)
        raise
    except Exception as e:
        print(f"[WAKE ERROR] {type(e).__name__}: {e} — retrying in 2s")
        import time as _time; _time.sleep(2)
        continue

    print("[AWAKE] Conversation mode active. Listening...")

    # --- Awake: continuous conversation loop ---
    while True:
        try:
            user_input = listen()
        except KeyboardInterrupt:
            save_memory(conversation_history)
            raise
        except Exception as e:
            print(f"[LISTEN ERROR] {type(e).__name__}: {e}")
            speak("Mic glitched, Boss. Say that again?")
            continue

        # Silence / nothing heard → go back to sleep
        if not user_input:
            print("[SLEEP] No input detected. Back to listening for wake word.")
            break

        print(f"You: {user_input}")
        lower = user_input.lower()

        # Hard shutdown
        if "shut down" in lower or "goodbye sara" in lower:
            speak("Shutting down. Later, Boss.")
            save_memory(conversation_history)
            exit(0)

        # Soft sleep — end conversation mode
        if any(phrase in lower for phrase in SLEEP_PHRASES):
            speak("Got it Boss. Just say Hey SARA when you need me.")
            break

        try:
            response = think(user_input)
        except KeyboardInterrupt:
            save_memory(conversation_history)
            raise
        except anthropic.RateLimitError:
            response = "I'm rate limited, Boss. Give me a minute and try again."
        except anthropic.APIConnectionError:
            response = "Can't reach the API, Boss. Check the network."
        except anthropic.APIStatusError as e:
            print(f"[API ERROR] {e.status_code}: {e}")
            response = "The API threw an error, Boss. Try that again."
        except Exception as e:
            print(f"[THINK ERROR] {type(e).__name__}: {e}")
            response = "Something broke on my end, Boss. Say that again and I'll take another run at it."

        print(f"SARA: {response}")
        speak(response)
        # Loop back — keep listening for follow-up without needing wake word