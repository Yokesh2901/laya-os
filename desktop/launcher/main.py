"""
LAYA OS - Custom Application Launcher
Futuristic GTK4/Libadwaita launcher with instant fuzzy search, Tamil phonetic search, and AI prompt bar.
"""

import sys
import os
from typing import List, Dict, Any, Optional

from system.hardware.apps import ApplicationManager
from desktop.theme.loader import apply_laya_theme
from laya.ai_core.agent import LayaAgent

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Adw
    _GTK_AVAILABLE = True
except (ImportError, ValueError):
    _GTK_AVAILABLE = False


class LayaLauncherWindow:
    """Application Launcher logic & catalog manager (UI-agnostic + testable)."""

    def __init__(self, app_manager: Optional[ApplicationManager] = None):
        self.apps_mgr = app_manager or ApplicationManager()
        self.all_apps = self.apps_mgr.scan_applications()
        self.filtered_apps = list(self.all_apps)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Filters applications based on English, Tamil, or Tanglish search query."""
        if not query or not query.strip():
            self.filtered_apps = list(self.all_apps)
            return self.filtered_apps

        q = query.strip().lower()
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
        return self.apps_mgr.launch(app_entry["exec"])


if _GTK_AVAILABLE:
    class LayaLauncherApp(Adw.Application):
        """GTK4/Libadwaita Application Launcher UI."""

        def __init__(self):
            super().__init__(application_id="org.laya.Launcher")
            self.logic = LayaLauncherWindow()
            self.agent = LayaAgent()
            self.connect("activate", self.on_activate)

        def on_activate(self, app):
            apply_laya_theme()

            win = Adw.ApplicationWindow(application=app)
            win.set_title("LAYA Launcher")
            win.set_default_size(760, 560)
            win.add_css_class("laya-launcher-window")

            root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            root_box.set_margin_top(24)
            root_box.set_margin_bottom(24)
            root_box.set_margin_start(28)
            root_box.set_margin_end(28)
            win.set_content(root_box)

            # Search Entry
            search_entry = Gtk.SearchEntry()
            search_entry.set_placeholder_text("Search apps or ask Laya (Tamil / English / Tanglish)...")
            search_entry.add_css_class("laya-search-bar")
            root_box.append(search_entry)

            # Laya AI Response Banner
            ai_reply_label = Gtk.Label(label="")
            ai_reply_label.add_css_class("laya-glass-card")
            ai_reply_label.set_wrap(True)
            ai_reply_label.set_visible(False)
            root_box.append(ai_reply_label)

            # App Grid Scrolled Window
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_vexpand(True)
            root_box.append(scrolled)

            flowbox = Gtk.FlowBox()
            flowbox.set_valign(Gtk.Align.START)
            flowbox.set_max_children_per_line(4)
            flowbox.set_min_children_per_line(2)
            flowbox.set_column_spacing(12)
            flowbox.set_row_spacing(12)
            flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scrolled.set_child(flowbox)

            def populate_apps(apps: List[Dict[str, Any]]):
                while child := flowbox.get_first_child():
                    flowbox.remove(child)
                for app_entry in apps[:40]:
                    btn = Gtk.Button()
                    btn.add_css_class("laya-app-card")
                    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
                    icon = Gtk.Image.new_from_icon_name(app_entry.get("icon", "application-x-executable"))
                    icon.set_pixel_size(40)
                    lbl = Gtk.Label(label=app_entry["name"])
                    lbl.set_max_width_chars(16)
                    lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
                    box.append(icon)
                    box.append(lbl)
                    btn.set_child(box)
                    btn.connect("clicked", lambda _b, entry=app_entry: (self.logic.launch_app(entry), win.close()))
                    flowbox.append(btn)

            populate_apps(self.logic.all_apps)

            def on_search_changed(entry):
                query = entry.get_text()
                results = self.logic.search(query)
                populate_apps(results)

            def on_search_activate(entry):
                query = entry.get_text().strip()
                if not query:
                    return
                if self.logic.filtered_apps and len(self.logic.filtered_apps) == 1:
                    self.logic.launch_app(self.logic.filtered_apps[0])
                    win.close()
                else:
                    res = self.agent.process_input(query)
                    ai_reply_label.set_text(f"Laya: {res.get('reply', '')}")
                    ai_reply_label.set_visible(True)

            search_entry.connect("search-changed", on_search_changed)
            search_entry.connect("activate", on_search_activate)

            win.present()


def main():
    if _GTK_AVAILABLE:
        app = LayaLauncherApp()
        sys.exit(app.run(sys.argv))
    else:
        launcher = LayaLauncherWindow()
        print(f"[LAYA OS Launcher] Indexed {len(launcher.all_apps)} applications (GTK4 unavailable).")


if __name__ == "__main__":
    main()
