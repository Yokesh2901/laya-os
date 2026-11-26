"""
LAYA OS - Custom Desktop Dock
Glassmorphic bottom dock featuring running application indicators, pinned favorites, and Laya AI Orb.
"""

import sys
import os
from typing import List, Dict, Any, Optional

from system.hardware.apps import ApplicationManager

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, GLib
    _GTK_AVAILABLE = True
except (ImportError, ValueError):
    _GTK_AVAILABLE = False


class LayaDock:
    """Glassmorphic Desktop Dock with Laya AI quick trigger."""

    DEFAULT_PINNED = [
        {"name": "Files", "exec": "nautilus", "icon": "system-file-manager"},
        {"name": "Browser", "exec": "google-chrome", "icon": "google-chrome"},
        {"name": "Terminal", "exec": "gnome-terminal", "icon": "utilities-terminal"},
        {"name": "Settings", "exec": "laya-settings", "icon": "preferences-system"},
    ]

    def __init__(self, app_manager: Optional[ApplicationManager] = None):
        self.app_mgr = app_manager or ApplicationManager()
        self.pinned_apps = list(self.DEFAULT_PINNED)
        self.is_laya_active = False

    def activate_laya_orb(self):
        """Toggles Laya voice assistant activation."""
        self.is_laya_active = not self.is_laya_active
        return {"laya_active": self.is_laya_active}

    def launch_pinned(self, index: int):
        """Launches a pinned application by index."""
        if 0 <= index < len(self.pinned_apps):
            app = self.pinned_apps[index]
            self.app_mgr.launch(app["exec"])
            return app
        return None


def main():
    dock = LayaDock()
    print(f"[LAYA OS Dock] Initialized with {len(dock.pinned_apps)} pinned applications.")


if __name__ == "__main__":
    main()
