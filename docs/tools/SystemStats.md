# Tool — System Stats

**Status:** ✅ Live  
**File:** `src/tools/system_stats.py`  
**Added:** v0.4.0  
**Dependency:** `psutil`

---

## What It Does

Real-time Mac hardware stats — CPU, RAM, battery, disk, and top processes.

---

## Voice Commands

| Say... | Action |
|---|---|
| *"How's the Mac doing?"* | `get_system_stats()` |
| *"What's my battery at?"* | `get_system_stats()` |
| *"What's eating my CPU?"* | `get_top_processes()` |
| *"How much storage is left?"* | `get_disk_usage()` |

---

## Functions

```python
get_system_stats() -> str
# Returns: "CPU: 12% | RAM: 7.4/17.2 GB (72%) | Battery: 80% (charging)"

get_top_processes(n: int = 5) -> str
# Returns: top N processes by CPU with RAM %

get_disk_usage(path: str = "/") -> str
# Returns: "Disk: 145/460 GB used (31%)"
```

---

## Implementation Notes

- `cpu_percent(interval=1)` — 1-second measurement for accuracy
- `sensors_battery()` returns `None` on desktops — handled gracefully
- Processes sorted by `cpu_percent` descending; filters `NoSuchProcess` and `AccessDenied`

---

## Dependency

```bash
pip install psutil
```
Already installed in `.venv-1`.

---

## See Also

- [[../SARA]] · [[../Roadmap]] · [[../Changelog]]
