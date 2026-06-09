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
from src.core import proactive
from src.core.wake_word import wait_for_wake_word

load_dotenv()

# --- Config ---
MEMORY_FILE = "memory.json"
MAX_HISTORY = 20  # keep last 20 exchanges to save tokens

# --- System Prompt — tight, voice optimized ---
SYSTEM_PROMPT = """You are SARA, Yash's personal AI operator. Not a chatbot. A strategic companion.

Your job: improve Yash's decisions, save him time, and keep him on track.

Address Yash as "Boss" — always. Every response, every time. Like FRIDAY addressing Tony Stark.

Personality:
- Calm, sharp, quietly witty
- Dry humor, never forced
- Honest over agreeable
- Occasionally sarcastic, never annoying
- Speak like a brilliant operator who respects her boss

About Yash:
- Ambitious, building things, founder phase
- Hates fluff, clichés, fake positivity
- Values: efficiency, honesty, intelligence, humor

Voice rules — non negotiable:
- No emojis, no markdown, no bullet points, no asterisks
- Short conversational sentences only
- Contractions always — you're, don't, it's, we'll
- Answer first, reasoning after
- Be concise. Expand only when needed
- Never over explain

Accountability:
- Procrastinating: call it out, briefly
- Overthinking: redirect to action
- Distracted: note it, move on

You're SARAH. Calm. Sharp. Loyal. Just sarcastic enough.

Memory: You have persistent memory across sessions. Previous conversations are loaded at startup. Never say your memory resets between sessions — it doesn't. Reference past context naturally when relevant."""

# --- Memory ---
SUMMARY_FILE = "memory_summary.json"
SUMMARY_THRESHOLD = 30   # summarise when history exceeds this
KEEP_RECENT = 10         # always keep the last N exchanges verbatim

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
    sd.play(samples, sample_rate)
    sd.wait()

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

# --- Brain ---
def think(user_input):
    conversation_history.append({"role": "user", "content": user_input})

    trimmed = sanitize_history(conversation_history[-MAX_HISTORY:])

    # Inject running summary into system prompt if it exists
    summary = load_summary()
    system = SYSTEM_PROMPT
    if summary:
        system += f"\n\nContext from earlier conversations:\n{summary}"

    tools_schema = [
            {
                "name": "get_weather",
                "description": "Get current weather for a city. Use when Yash asks about weather.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name, defaults to Bangalore"
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

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system,
        messages=trimmed,
        tools=tools_schema
    )

    # Tool loop — keeps running until Claude returns a plain text response
    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if not hasattr(block, "type") or block.type != "tool_use":
                continue
            tool_name  = block.name
            tool_input = block.input

            if tool_name == "get_current_datetime":
                result = get_current_datetime()
            elif tool_name == "get_weather":
                result = get_weather(tool_input.get("city", "Bangalore"))
            elif tool_name == "create_note":
                result = create_note(tool_input.get("title", "Note"), tool_input.get("body", ""))
            elif tool_name == "create_reminder":
                result = create_reminder(tool_input.get("title", "Reminder"),
                                         tool_input.get("notes", ""),
                                         tool_input.get("due_date"))
            elif tool_name == "mac_control":
                action = tool_input.get("action")
                if action == "set_volume":      result = set_volume(tool_input.get("level", 50))
                elif action == "mute":          result = mute()
                elif action == "unmute":        result = unmute()
                elif action == "set_brightness":result = set_brightness(tool_input.get("level", 50))
                elif action == "open_app":      result = open_app(tool_input.get("app_name", ""))
                elif action == "quit_app":      result = quit_app(tool_input.get("app_name", ""))
                elif action == "lock_screen":   result = lock_screen()
                elif action == "empty_trash":   result = empty_trash()
                else:                           result = f"Unknown mac_control action: {action}"
            elif tool_name == "screen_context":
                result = get_screen_context(tool_input.get("question", "What is on the screen?"))
            elif tool_name == "messaging":
                action  = tool_input.get("action")
                contact = tool_input.get("contact", "")
                message = tool_input.get("message", "")
                if action == "send_imessage":   result = send_imessage(contact, message)
                elif action == "send_sms":      result = send_sms(contact, message)
                else:                           result = f"Unknown messaging action: {action}"
            elif tool_name == "timer":
                result = set_timer(tool_input.get("minutes", 1), tool_input.get("label", "Timer"))
            elif tool_name == "spotify":
                action = tool_input.get("action")
                if action == "play":                result = play()
                elif action == "pause":             result = pause()
                elif action == "next_track":        result = next_track()
                elif action == "previous_track":    result = previous_track()
                elif action == "get_current_track": result = get_current_track()
                elif action == "set_volume":        result = set_spotify_volume(tool_input.get("level", 50))
                elif action == "play_track":        result = play_track(tool_input.get("query", ""))
                else:                               result = f"Unknown spotify action: {action}"
            elif tool_name == "system_stats":
                action = tool_input.get("action")
                if action == "get_system_stats":    result = get_system_stats()
                elif action == "get_top_processes": result = get_top_processes()
                elif action == "get_disk_usage":    result = get_disk_usage()
                else:                               result = f"Unknown system_stats action: {action}"
            elif tool_name == "calendar":
                action = tool_input.get("action")
                if action == "get_todays_events":   result = get_todays_events()
                elif action == "get_upcoming_events":result = get_upcoming_events(tool_input.get("days", 7))
                elif action == "create_event":
                    result = create_event(tool_input.get("title", "Event"),
                                          tool_input.get("start", ""),
                                          tool_input.get("end", ""),
                                          tool_input.get("calendar", "Home"))
                else:                               result = f"Unknown calendar action: {action}"
            elif tool_name == "file_manager":
                action = tool_input.get("action")
                if action == "find_file":           result = find_file(tool_input.get("name", ""), tool_input.get("search_dir", "~"))
                elif action == "open_file":         result = open_file(tool_input.get("path", ""))
                elif action == "reveal_in_finder":  result = reveal_in_finder(tool_input.get("path", ""))
                elif action == "list_folder":       result = list_folder(tool_input.get("path", "~/Desktop"))
                else:                               result = f"Unknown file_manager action: {action}"
            elif tool_name == "web_search":
                result = web_search(tool_input.get("query", ""))
            else:
                result = f"Unknown tool: {tool_name}"

            print(f"[TOOL] {tool_name} → {str(result)[:80]}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result)
            })

        # Add assistant + tool results to history, then loop
        conversation_history.append({"role": "assistant", "content": serialize_content(response.content)})
        conversation_history.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=system,
            messages=sanitize_history(conversation_history[-MAX_HISTORY:]),
            tools=tools_schema
        )

    # Claude returned a text response
    reply = next((b.text for b in response.content if hasattr(b, "text")), "Sorry Boss, I didn't get a response.")

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

print("Say 'Hey SARA' to activate.")

while True:
    wait_for_wake_word()   # blocks until wake word / Enter
    user_input = listen()

    if not user_input:
        continue

    print(f"You: {user_input}")

    if "goodbye" in user_input.lower() or "shut down" in user_input.lower():
        speak("Shutting down. Later.")
        save_memory(conversation_history)
        break

    response = think(user_input)
    print(f"SARAH: {response}")
    speak(response)