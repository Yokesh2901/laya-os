"""
LAYA OS - Audio Subsystem Integration
Interfaces with Linux PipeWire / WirePlumber (via wpctl/pamixer) for master volume and mute controls.
"""

import subprocess
import shutil
from typing import Dict, Any, Tuple


class AudioManager:
    """Manages audio volume and mute state via PipeWire or PulseAudio CLI interfaces."""

    def __init__(self):
        self.wpctl_path = shutil.which("wpctl")
        self.pamixer_path = shutil.which("pamixer")
        self.amixer_path = shutil.which("amixer")
        self._mock_volume = 65
        self._mock_mute = False

    def get_volume(self) -> Dict[str, Any]:
        """Returns current volume percentage and mute status."""
        if self.wpctl_path:
            try:
                out = subprocess.check_output(
                    [self.wpctl_path, "get-volume", "@DEFAULT_AUDIO_SINK@"],
                    stderr=subprocess.DEVNULL,
                    text=True
                ).strip()
                # Output format e.g.: "Volume: 0.65 [MUTED]" or "Volume: 0.65"
                parts = out.split()
                if len(parts) >= 2 and parts[0].lower() == "volume:":
                    vol = int(float(parts[1]) * 100)
                    is_muted = "[MUTED]" in out
                    return {"volume": vol, "muted": is_muted, "driver": "pipewire-wpctl", "status": "ok"}
            except Exception:
                pass

        if self.pamixer_path:
            try:
                vol_str = subprocess.check_output([self.pamixer_path, "--get-volume"], stderr=subprocess.DEVNULL, text=True).strip()
                mute_str = subprocess.check_output([self.pamixer_path, "--get-mute"], stderr=subprocess.DEVNULL, text=True).strip()
                return {
                    "volume": int(vol_str),
                    "muted": mute_str.lower() == "true",
                    "driver": "pulseaudio-pamixer",
                    "status": "ok"
                }
            except Exception:
                pass

        # Fallback / testing environment response
        return {
            "volume": self._mock_volume,
            "muted": self._mock_mute,
            "driver": "software-emulated",
            "status": "ok"
        }

    def set_volume(self, volume_percent: int) -> Tuple[bool, str]:
        """Sets the audio volume to a target percentage (0-100)."""
        clamped = max(0, min(100, int(volume_percent)))

        if self.wpctl_path:
            try:
                val = clamped / 100.0
                subprocess.check_call(
                    [self.wpctl_path, "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val:.2f}"],
                    stderr=subprocess.DEVNULL
                )
                return True, f"Volume set to {clamped}% via wpctl."
            except Exception as e:
                return False, f"PipeWire error: {e}"

        if self.pamixer_path:
            try:
                subprocess.check_call(
                    [self.pamixer_path, "--set-volume", str(clamped)],
                    stderr=subprocess.DEVNULL
                )
                return True, f"Volume set to {clamped}% via pamixer."
            except Exception as e:
                return False, f"PulseAudio error: {e}"

        self._mock_volume = clamped
        return True, f"Volume set to {clamped}% (emulated)."

    def set_mute(self, muted: bool) -> Tuple[bool, str]:
        """Toggles or sets the audio mute state."""
        if self.wpctl_path:
            try:
                arg = "1" if muted else "0"
                subprocess.check_call(
                    [self.wpctl_path, "set-mute", "@DEFAULT_AUDIO_SINK@", arg],
                    stderr=subprocess.DEVNULL
                )
                return True, f"Audio {'muted' if muted else 'unmuted'} via wpctl."
            except Exception as e:
                return False, f"PipeWire error: {e}"

        if self.pamixer_path:
            try:
                flag = "--mute" if muted else "--unmute"
                subprocess.check_call([self.pamixer_path, flag], stderr=subprocess.DEVNULL)
                return True, f"Audio {'muted' if muted else 'unmuted'} via pamixer."
            except Exception as e:
                return False, f"PulseAudio error: {e}"

        self._mock_mute = bool(muted)
        return True, f"Audio {'muted' if muted else 'unmuted'} (emulated)."
