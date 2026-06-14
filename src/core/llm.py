"""
LLM compatibility layer.

Exposes an `LLMClient` whose `.messages.create(...)` quacks exactly like the
Anthropic SDK — same `system=` / `messages=` / `tools=` inputs, same
`.stop_reason` + `.content` blocks on the way out — but talks to an
OpenAI-compatible endpoint (a local MLX server) underneath.

This lets the rest of SARA keep working in Anthropic response shape:
the tool loop, serialize_content(), sanitize_history(), and the on-disk
memory.json format are all untouched. Only main.py / proactive.py swap which
client they instantiate.

Config (env):
    LOCAL_API_BASE   default http://localhost:8080/v1
    LOCAL_MODEL      default mlx-community/Qwen2.5-Coder-14B-Instruct-4bit
"""

import os
import json

from openai import OpenAI


DEFAULT_BASE  = "http://localhost:8080/v1"
DEFAULT_MODEL = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"


class LLMError(Exception):
    """Raised for any failure talking to the local model — connection refused,
    bad response, etc. The brain catches this and speaks a graceful message
    instead of crashing."""


# --- Anthropic-shaped response objects ------------------------------------

class _TextBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class _ToolUseBlock:
    type = "tool_use"

    def __init__(self, id, name, input):
        self.id = id
        self.name = name
        self.input = input


class _Response:
    """Mimics anthropic's Message: has .stop_reason and .content (list of blocks)."""

    def __init__(self, stop_reason, content):
        self.stop_reason = stop_reason   # "tool_use" | "end_turn"
        self.content = content


# --- Translation: Anthropic shape <-> OpenAI shape ------------------------

def _flatten_system(system):
    """system may be a string or a list of {"type":"text","text":...} blocks
    (with optional cache_control, which has no local equivalent — ignored)."""
    if not system:
        return None
    if isinstance(system, str):
        return system
    parts = []
    for block in system:
        if isinstance(block, dict):
            txt = block.get("text", "")
        else:
            txt = getattr(block, "text", "")
        if txt:
            parts.append(txt)
    return "\n\n".join(parts) if parts else None


def _to_openai_messages(system, messages):
    out = []
    sys_text = _flatten_system(system)
    if sys_text:
        out.append({"role": "system", "content": sys_text})

    for msg in messages or []:
        role = msg["role"]
        content = msg.get("content")

        # Plain string content (normal user/assistant turns)
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue

        if not isinstance(content, list):
            continue

        if role == "assistant":
            # May hold text blocks and/or tool_use blocks
            text_parts, tool_calls = [], []
            for blk in content:
                btype = blk.get("type") if isinstance(blk, dict) else getattr(blk, "type", None)
                if btype == "text":
                    text_parts.append(blk["text"] if isinstance(blk, dict) else blk.text)
                elif btype == "tool_use":
                    bid   = blk["id"]    if isinstance(blk, dict) else blk.id
                    bname = blk["name"]  if isinstance(blk, dict) else blk.name
                    binp  = blk["input"] if isinstance(blk, dict) else blk.input
                    tool_calls.append({
                        "id": bid,
                        "type": "function",
                        "function": {"name": bname, "arguments": json.dumps(binp)},
                    })
            assistant_msg = {"role": "assistant",
                             "content": "\n".join(text_parts) if text_parts else None}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            out.append(assistant_msg)

        elif role == "user":
            # List form is a batch of tool_result blocks. OpenAI wants one
            # {"role":"tool"} message per tool_call_id, in order.
            for blk in content:
                btype = blk.get("type") if isinstance(blk, dict) else getattr(blk, "type", None)
                if btype == "tool_result":
                    out.append({
                        "role": "tool",
                        "tool_call_id": blk["tool_use_id"],
                        "content": str(blk.get("content", "")),
                    })
                elif btype == "text":
                    out.append({"role": "user", "content": blk["text"]})

    return out


def _to_openai_tools(tools):
    if not tools:
        return None
    return [{
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t.get("description", ""),
            "parameters": t["input_schema"],
        },
    } for t in tools]


def _from_openai_response(resp):
    choice = resp.choices[0]
    msg = choice.message

    blocks = []
    if getattr(msg, "content", None):
        blocks.append(_TextBlock(msg.content))

    tool_calls = getattr(msg, "tool_calls", None) or []
    for tc in tool_calls:
        try:
            args = json.loads(tc.function.arguments or "{}")
        except (json.JSONDecodeError, TypeError):
            args = {}
        blocks.append(_ToolUseBlock(tc.id, tc.function.name, args))

    stop_reason = "tool_use" if tool_calls else "end_turn"
    return _Response(stop_reason, blocks)


# --- The client -----------------------------------------------------------

class _Messages:
    def __init__(self, client, default_model):
        self._client = client
        self._default_model = default_model

    def create(self, model=None, max_tokens=512, system=None, messages=None, tools=None):
        oai_messages = _to_openai_messages(system, messages)
        oai_tools = _to_openai_tools(tools)

        kwargs = {
            "model": model or self._default_model,
            "max_tokens": max_tokens,
            "messages": oai_messages,
        }
        # Only send tool keys when we actually have tools — some MLX servers
        # reject an explicit null.
        if oai_tools:
            kwargs["tools"] = oai_tools
            kwargs["tool_choice"] = "auto"

        try:
            resp = self._client.chat.completions.create(**kwargs)
        except Exception as e:
            raise LLMError(str(e)) from e

        return _from_openai_response(resp)


class LLMClient:
    """Drop-in stand-in for anthropic.Anthropic() backed by a local MLX server."""

    def __init__(self, base_url=None, model=None, api_key="not-needed"):
        self.base_url = base_url or os.getenv("LOCAL_API_BASE", DEFAULT_BASE)
        self.model = model or os.getenv("LOCAL_MODEL", DEFAULT_MODEL)
        self._client = OpenAI(base_url=self.base_url, api_key=api_key)
        self.messages = _Messages(self._client, self.model)


def probe_server(client: LLMClient) -> bool:
    """Best-effort boot check. Prints a clear warning if the server is
    unreachable. Tool-calling support is confirmed on the first real call."""
    try:
        client._client.models.list()
        print(f"[LLM] Local model server reachable at {client.base_url} (model: {client.model})")
        print("[LLM] Tool-calling support is verified on first use — watch for [TOOL] lines.")
        return True
    except Exception as e:
        print(f"[LLM] WARNING: can't reach local model server at {client.base_url} — {e}")
        print("[LLM] Start it with:  mlx-omni-server --port 8080")
        return False
