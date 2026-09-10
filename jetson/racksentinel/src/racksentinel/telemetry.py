from __future__ import annotations

import glob
import json
import os
import platform
import shutil
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "aari.racksentinel.telemetry.v1"


def _read_text(path: str | Path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except (OSError, PermissionError):
        return None


def _temperature_c(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if abs(value) >= 1000:
        value /= 1000.0
    return round(value, 2)


def collect_thermal_zones(pattern: str = "/sys/class/thermal/thermal_zone*") -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    for zone_path in sorted(glob.glob(pattern)):
        name = _read_text(Path(zone_path) / "type") or Path(zone_path).name
        value = _temperature_c(_read_text(Path(zone_path) / "temp"))
        if value is not None:
            zones.append({"name": name, "temperature_c": value})
    return zones


def collect_memory(meminfo_path: str | Path = "/proc/meminfo") -> dict[str, float | None]:
    raw = _read_text(meminfo_path)
    if not raw:
        return {"total_mb": None, "available_mb": None, "used_percent": None}
    values: dict[str, int] = {}
    for line in raw.splitlines():
        key, _, rest = line.partition(":")
        if not rest:
            continue
        token = rest.strip().split()[0]
        try:
            values[key] = int(token)
        except ValueError:
            continue
    total_kb = values.get("MemTotal")
    available_kb = values.get("MemAvailable")
    used_percent = None
    if total_kb and available_kb is not None:
        used_percent = round((total_kb - available_kb) * 100 / total_kb, 2)
    return {
        "total_mb": round(total_kb / 1024, 2) if total_kb else None,
        "available_mb": round(available_kb / 1024, 2) if available_kb is not None else None,
        "used_percent": used_percent,
    }


def collect_gpu_load(paths: Iterable[str] | None = None) -> float | None:
    candidates = list(paths or (
        "/sys/devices/platform/17000000.gpu/load",
        "/sys/devices/gpu.0/load",
    ))
    for path in candidates:
        raw = _read_text(path)
        if raw is None:
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        if value > 100:
            value /= 10.0
        return round(min(max(value, 0.0), 100.0), 2)
    return None


def collect_power_mode() -> str | None:
    try:
        result = subprocess.run(
            ["nvpmodel", "-q"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None


def collect_model() -> str | None:
    return _read_text("/proc/device-tree/model")


def evaluate_health(
    zones: list[dict[str, Any]],
    warning_temp_c: float,
    critical_temp_c: float,
) -> dict[str, Any]:
    temperatures = [z["temperature_c"] for z in zones if z.get("temperature_c") is not None]
    max_temp = max(temperatures) if temperatures else None
    status = "ok"
    reasons: list[str] = []
    if max_temp is None:
        status = "unknown"
        reasons.append("No thermal sensor data available")
    elif max_temp >= critical_temp_c:
        status = "critical"
        reasons.append(f"Temperature {max_temp:.1f} C meets critical threshold")
    elif max_temp >= warning_temp_c:
        status = "warning"
        reasons.append(f"Temperature {max_temp:.1f} C meets warning threshold")
    return {"status": status, "max_temperature_c": max_temp, "reasons": reasons}


@dataclass(frozen=True)
class Settings:
    site_id: str = "local-lab"
    node_role: str = "jetson-edge"
    warning_temp_c: float = 80.0
    critical_temp_c: float = 90.0
    data_path: str = "/var/lib/aari-racksentinel/telemetry.jsonl"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            site_id=os.getenv("AARI_SITE_ID", cls.site_id),
            node_role=os.getenv("AARI_NODE_ROLE", cls.node_role),
            warning_temp_c=float(os.getenv("AARI_WARNING_TEMP_C", str(cls.warning_temp_c))),
            critical_temp_c=float(os.getenv("AARI_CRITICAL_TEMP_C", str(cls.critical_temp_c))),
            data_path=os.getenv("AARI_DATA_PATH", cls.data_path),
        )


def collect(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    zones = collect_thermal_zones()
    disk = shutil.disk_usage("/")
    try:
        load_1m, load_5m, load_15m = os.getloadavg()
    except OSError:
        load_1m = load_5m = load_15m = None
    uptime_raw = _read_text("/proc/uptime")
    uptime_seconds = None
    if uptime_raw:
        try:
            uptime_seconds = round(float(uptime_raw.split()[0]), 2)
        except (ValueError, IndexError):
            pass
    event = {
        "schema": SCHEMA,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "site_id": settings.site_id,
        "node": socket.gethostname(),
        "node_role": settings.node_role,
        "platform": {
            "model": collect_model(),
            "machine": platform.machine(),
            "kernel": platform.release(),
            "python": platform.python_version(),
        },
        "compute": {
            "cpu_count": os.cpu_count(),
            "load_1m": load_1m,
            "load_5m": load_5m,
            "load_15m": load_15m,
            "gpu_load_percent": collect_gpu_load(),
            "power_mode": collect_power_mode(),
        },
        "memory": collect_memory(),
        "storage": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "used_percent": round(disk.used * 100 / disk.total, 2),
        },
        "thermal": {"zones": zones},
        "uptime_seconds": uptime_seconds,
    }
    event["health"] = evaluate_health(
        zones,
        warning_temp_c=settings.warning_temp_c,
        critical_temp_c=settings.critical_temp_c,
    )
    return event


def append_jsonl(event: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, separators=(",", ":")) + "\n")

