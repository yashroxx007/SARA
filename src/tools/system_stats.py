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
    procs = []
    for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x["cpu_percent"] or 0, reverse=True)
    top = procs[:n]
    lines = [f"{p['name']} — CPU {p['cpu_percent']:.1f}%, RAM {p['memory_percent']:.1f}%" for p in top]
    return "Top processes:\n" + "\n".join(lines)


def get_disk_usage(path: str = "/") -> str:
    usage = psutil.disk_usage(path)
    used = round(usage.used / 1e9, 1)
    total = round(usage.total / 1e9, 1)
    pct = usage.percent
    return f"Disk: {used}/{total} GB used ({pct}%)"
