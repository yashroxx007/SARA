import subprocess
import os
import glob


def find_file(name: str, search_dir: str = "~") -> str:
    """Find files matching a name pattern under search_dir."""
    search_dir = os.path.expanduser(search_dir)
    pattern = f"**/*{name}*"
    try:
        matches = glob.glob(os.path.join(search_dir, pattern), recursive=True)
        # Exclude hidden/system dirs for speed
        matches = [m for m in matches if "/.Trash" not in m and "/Library/" not in m][:8]
        if not matches:
            return f"No files matching '{name}' found in {search_dir}."
        return "Found:\n" + "\n".join(matches)
    except Exception as e:
        return f"Search error: {e}"


def open_file(path: str) -> str:
    """Open a file with its default app."""
    path = os.path.expanduser(path)
    result = subprocess.run(["open", path], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't open file: {result.stderr.strip()}"
    return f"Opened {os.path.basename(path)}."


def reveal_in_finder(path: str) -> str:
    """Show a file in Finder."""
    path = os.path.expanduser(path)
    result = subprocess.run(["open", "-R", path], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't reveal file: {result.stderr.strip()}"
    return f"Revealed {os.path.basename(path)} in Finder."


def list_folder(path: str = "~/Desktop") -> str:
    """List contents of a folder."""
    path = os.path.expanduser(path)
    try:
        items = os.listdir(path)
        items = [i for i in items if not i.startswith(".")]
        if not items:
            return f"{path} is empty."
        return f"{len(items)} items in {os.path.basename(path)}: " + ", ".join(items[:15])
    except Exception as e:
        return f"Couldn't list folder: {e}"
