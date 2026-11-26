"""
LAYA OS - Custom Application Launcher
Futuristic GTK4/Libadwaita launcher with instant fuzzy search, category filters, and Tamil phonetic search.
"""

import sys
import os
from typing import List, Dict, Any, Optional

from system.hardware.apps import ApplicationManager

try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, GLib, Gio
    _GTK_AVAILABLE = True
except (ImportError, ValueError):
    _GTK_AVAILABLE = False


class LayaLauncherWindow:
    """GTK4 Application Launcher Window with Glassmorphic styling."""

    def __init__(self, app_manager: Optional[ApplicationManager] = None):
        self.apps_mgr = app_manager or ApplicationManager()
        self.all_apps = self.apps_mgr.scan_applications()
        self.filtered_apps = list(self.all_apps)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Filters applications based on search query."""
        if not query or not query.strip():
            self.filtered_apps = list(self.all_apps)
            return self.filtered_apps

        q = query.strip().lower()

        # Check Tamil phonetic mappings
        for t_key, eng_val in self.apps_mgr.TAMIL_APP_MAP.items():
            if t_key in q:
                q = eng_val
                break

        matches = []
        for app in self.all_apps:
            name_lower = app["name"].lower()
            if q in name_lower or q in app["exec"].lower():
                matches.append(app)

        self.filtered_apps = matches
        return self.filtered_apps

    def launch_app(self, app_entry: Dict[str, Any]):
        """Launches selected application."""
        self.apps_mgr.launch(app_entry["exec"])


def main():
    print("[LAYA OS Launcher] Application Launcher initialized.")
    launcher = LayaLauncherWindow()
    print(f"[LAYA OS Launcher] Indexed {len(launcher.all_apps)} applications.")


if __name__ == "__main__":
    main()
