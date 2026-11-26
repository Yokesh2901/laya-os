"""
LAYA OS - Hardware & System Telemetry Monitor
Reads real-time CPU, RAM, disk, battery, and network performance indicators.
"""

import os
import sys
import time
from typing import Dict, Any, Optional

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False


class SystemMonitor:
    """Reads system load and resource consumption for Laya OS."""

    def __init__(self):
        self._last_net_io = None
        self._last_net_time = 0.0

    def get_system_summary(self) -> Dict[str, Any]:
        """Returns comprehensive resource statistics."""
        stats: Dict[str, Any] = {
            "platform": sys.platform,
            "timestamp": time.time(),
            "cpu_percent": 0.0,
            "cpu_count": os.cpu_count() or 1,
            "memory": {
                "total_mb": 0,
                "available_mb": 0,
                "used_mb": 0,
                "percent": 0.0
            },
            "disk": {
                "total_gb": 0.0,
                "used_gb": 0.0,
                "free_gb": 0.0,
                "percent": 0.0
            },
            "battery": None,
            "status": "ok"
        }

        if _PSUTIL_AVAILABLE:
            try:
                stats["cpu_percent"] = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                stats["memory"] = {
                    "total_mb": round(mem.total / (1024 * 1024), 1),
                    "available_mb": round(mem.available / (1024 * 1024), 1),
                    "used_mb": round(mem.used / (1024 * 1024), 1),
                    "percent": mem.percent
                }

                disk = psutil.disk_usage('/')
                stats["disk"] = {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent
                }

                batt = psutil.sensors_battery()
                if batt:
                    stats["battery"] = {
                        "percent": batt.percent,
                        "power_plugged": batt.power_plugged,
                        "secsleft": batt.secsleft
                    }
            except Exception as e:
                stats["error"] = str(e)
                stats["status"] = "partial"
        else:
            # Fallback for Linux environments without psutil installed yet
            if sys.platform.startswith("linux") and os.path.exists("/proc/meminfo"):
                try:
                    with open("/proc/meminfo", "r") as f:
                        lines = f.readlines()
                    meminfo = {}
                    for line in lines:
                        parts = line.split(":")
                        if len(parts) == 2:
                            meminfo[parts[0].strip()] = parts[1].strip()
                    total_kb = int(meminfo.get("MemTotal", "0 kB").split()[0])
                    avail_kb = int(meminfo.get("MemAvailable", "0 kB").split()[0])
                    used_kb = total_kb - avail_kb
                    stats["memory"] = {
                        "total_mb": round(total_kb / 1024, 1),
                        "available_mb": round(avail_kb / 1024, 1),
                        "used_mb": round(used_kb / 1024, 1),
                        "percent": round((used_kb / total_kb) * 100, 1) if total_kb > 0 else 0.0
                    }
                except Exception:
                    pass

        return stats
