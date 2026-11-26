"""
LAYA OS - Display & Brightness Subsystem
Controls screen brightness via brightnessctl or sysfs backlight interface.
"""

import os
import shutil
import subprocess
from typing import Dict, Any, Tuple


class DisplayManager:
    """Controls screen backlight and display settings on Linux."""

    def __init__(self):
        self.brightnessctl_path = shutil.which("brightnessctl")
        self._mock_brightness = 70

    def get_brightness(self) -> Dict[str, Any]:
        """Returns the current screen brightness percentage."""
        if self.brightnessctl_path:
            try:
                # e.g., output: "70%" or "175000/250000 (70%)"
                out = subprocess.check_output(
                    [self.brightnessctl_path, "get"],
                    stderr=subprocess.DEVNULL,
                    text=True
                ).strip()
                max_out = subprocess.check_output(
                    [self.brightnessctl_path, "max"],
                    stderr=subprocess.DEVNULL,
                    text=True
                ).strip()
                curr_val = float(out)
                max_val = float(max_out)
                pct = int((curr_val / max_val) * 100) if max_val > 0 else 0
                return {"brightness": pct, "driver": "brightnessctl", "status": "ok"}
            except Exception:
                pass

        # Check sysfs backlight directly
        sysfs_base = "/sys/class/backlight"
        if os.path.exists(sysfs_base):
            try:
                devices = os.listdir(sysfs_base)
                if devices:
                    dev_path = os.path.join(sysfs_base, devices[0])
                    with open(os.path.join(dev_path, "brightness"), "r") as f:
                        curr = float(f.read().strip())
                    with open(os.path.join(dev_path, "max_brightness"), "r") as f:
                        max_b = float(f.read().strip())
                    pct = int((curr / max_b) * 100) if max_b > 0 else 0
                    return {"brightness": pct, "driver": "sysfs", "status": "ok"}
            except Exception:
                pass

        return {"brightness": self._mock_brightness, "driver": "emulated", "status": "ok"}

    def set_brightness(self, percent: int) -> Tuple[bool, str]:
        """Sets brightness to requested percentage (0-100)."""
        clamped = max(5, min(100, int(percent)))

        if self.brightnessctl_path:
            try:
                subprocess.check_call(
                    [self.brightnessctl_path, "set", f"{clamped}%"],
                    stderr=subprocess.DEVNULL
                )
                return True, f"Brightness set to {clamped}% via brightnessctl."
            except Exception as e:
                return False, f"brightnessctl error: {e}"

        self._mock_brightness = clamped
        return True, f"Brightness set to {clamped}% (emulated)."
