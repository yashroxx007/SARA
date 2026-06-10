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


def get_project(name: str) -> str:
    f = _find_project(name)
    if not f:
        return f"No project matching '{name}'. Projects: {list_projects()}"
    with open(os.path.join(PROJECTS_DIR, f)) as fh:
        return fh.read()


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
