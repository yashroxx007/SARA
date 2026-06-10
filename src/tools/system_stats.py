import time
import psutil
import subprocess


def get_system_stats() -> str:
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_used = round(ram.used / 1e9, 1)
    ram_total = round(ram.total / 1e9, 1)
    ram_pct = ram.percent

    battery = psutil.sensors_battery()
    if battery:
        batt_pct = round(battery.percent)
        charging = "charging" if battery.power_plugged else "on battery"
        batt_str = f"{batt_pct}% ({charging})"
    else:
        batt_str = "no battery info"

    return (
        f"CPU: {cpu}% | "
        f"RAM: {ram_used}/{ram_total} GB ({ram_pct}%) | "
        f"Battery: {batt_str}"
    )


def get_top_processes(n: int = 5) -> str:
    # First pass: initialise cpu_percent counters (always returns 0 on first call)
    procs = {}
    for p in psutil.process_iter(["name", "memory_percent"]):
        try:
            p.cpu_percent()
            procs[p.pid] = p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    time.sleep(0.5)  # give psutil a measurement window

    results = []
    for p in procs.values():
        try:
            cpu = p.cpu_percent()
            mem = p.info.get("memory_percent") or 0
            results.append({"name": p.info["name"], "cpu": cpu, "mem": mem})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    results.sort(key=lambda x: x["cpu"], reverse=True)
    # Prefer processes actually using CPU; fall back to top-n if all idle
    top = [r for r in results if r["cpu"] > 0][:n] or results[:n]
    lines = [f"{r['name']} — CPU {r['cpu']:.1f}%, RAM {r['mem']:.1f}%" for r in top]
    return "Top processes by CPU:\n" + "\n".join(lines)


def get_disk_usage(path: str = "/") -> str:
    usage = psutil.disk_usage(path)
    used = round(usage.used / 1e9, 1)
    total = round(usage.total / 1e9, 1)
    pct = usage.percent
    return f"Disk: {used}/{total} GB used ({pct}%)"
