"""
Project knowledge — SARA's awareness of what Yash is building.
One markdown file per project in projects/. Readable and writable by voice,
and by Claude Code sessions in other repos (they write to the same folder).
"""

import os
import re
from datetime import datetime

PROJECTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "projects",
)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _find_project(name: str) -> str | None:
    """Fuzzy match a spoken project name to a file. 'the instagram project'
    matches instagram-content.md."""
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    files = [f for f in os.listdir(PROJECTS_DIR) if f.endswith(".md")]
    wanted = set(_slug(name).split("-"))
    best, best_score = None, 0
    for f in files:
        words = set(f[:-3].split("-"))
        score = len(wanted & words)
        if score > best_score:
            best, best_score = f, score
    return best if best_score > 0 else None


def list_projects() -> str:
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    files = sorted(f for f in os.listdir(PROJECTS_DIR) if f.endswith(".md"))
    if not files:
        return "No projects yet."
    lines = []
    for f in files:
        path = os.path.join(PROJECTS_DIR, f)
        with open(path) as fh:
            content = fh.read()
        # First non-empty line after the title is the one-liner
        body = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
        summary = body[0] if body else "(empty)"
        lines.append(f"{f[:-3]}: {summary}")
    return "\n".join(lines)


MAX_SOURCE_CHARS = 8000  # per linked source, keep token cost sane


def _read_source(path: str) -> str:
    """Read a linked source — a markdown file, or a directory (Obsidian vault):
    all top-level .md files, newest first, capped."""
    path = os.path.expanduser(path.strip())
    if os.path.isfile(path):
        with open(path) as fh:
            return fh.read()[:MAX_SOURCE_CHARS]
    if os.path.isdir(path):
        md_files = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.endswith(".md"):
                    full = os.path.join(root, f)
                    md_files.append((os.path.getmtime(full), os.path.relpath(full, path), full))
        md_files.sort(reverse=True)  # newest first

        parts, used, skipped = [], 0, []
        for _, rel, full in md_files:
            with open(full) as fh:
                content = fh.read()
            chunk = f"--- {rel} ---\n{content}"
            if used + len(chunk) > MAX_SOURCE_CHARS:
                skipped.append(rel)
                continue
            parts.append(chunk)
            used += len(chunk)
        if skipped:
            parts.append(f"--- (older/larger files not shown: {', '.join(skipped)}) ---")
        return "\n\n".join(parts) if parts else "(no markdown files found)"
    return f"(source not found: {path})"


def get_project(name: str) -> str:
    f = _find_project(name)
    if not f:
        return f"No project matching '{name}'. Projects: {list_projects()}"
    with open(os.path.join(PROJECTS_DIR, f)) as fh:
        content = fh.read()

    # Follow `source:` pointers — live files/vaults elsewhere on the Mac
    out = [content]
    for line in content.splitlines():
        if line.lower().startswith("source:"):
            src = line.split(":", 1)[1]
            out.append(f"\n=== Linked source ({src.strip()}) ===\n{_read_source(src)}")
    return "\n".join(out)


def update_project(name: str, note: str) -> str:
    f = _find_project(name)
    if not f:
        return f"No project matching '{name}'. Use create_project first."
    path = os.path.join(PROJECTS_DIR, f)
    stamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
    with open(path, "a") as fh:
        fh.write(f"\n- **{stamp}** — {note}")
    return f"Logged to {f[:-3]}."


def create_project(name: str, description: str = "") -> str:
    slug = _slug(name)
    path = os.path.join(PROJECTS_DIR, f"{slug}.md")
    if os.path.exists(path):
        return f"Project '{slug}' already exists."
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    with open(path, "w") as fh:
        fh.write(f"# {name}\n\n{description}\n\n## Current Focus\n\n\n## Log\n")
    return f"Project '{slug}' created."
