"""
LAYA OS - Custom Desktop Dock
Glassmorphic bottom dock featuring pinned favorites, launcher button, and Laya AI Orb.
"""

import sys
from typing import Optional

from system.hardware.apps import ApplicationManager
from desktop.theme.loader import apply_laya_theme

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Adw
    _GTK_AVAILABLE = True
except (ImportError, ValueError):
    _GTK_AVAILABLE = False


class LayaDock:
    """Glassmorphic Desktop Dock state & launcher logic."""

    DEFAULT_PINNED = [
        {"name": "Files", "exec": "nautilus", "icon": "system-file-manager"},
        {"name": "Browser", "exec": "google-chrome", "icon": "web-browser"},
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


if _GTK_AVAILABLE:
    class LayaDockApp(Adw.Application):
        """GTK4 Floating Glassmorphic Dock Window."""

        def __init__(self):
            super().__init__(application_id="org.laya.Dock")
            self.logic = LayaDock()
            self.connect("activate", self.on_activate)

        def on_activate(self, app):
            apply_laya_theme()

            win = Gtk.ApplicationWindow(application=app)
            win.set_title("LAYA Dock")
            win.set_decorated(False)
            win.set_resizable(False)
            win.add_css_class("laya-window")

            dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            dock_box.add_css_class("laya-dock-container")
            win.set_child(dock_box)

            # App Launcher Grid Button
            launcher_btn = Gtk.Button()
            launcher_btn.add_css_class("laya-dock-item")
            launcher_btn.set_tooltip_text("LAYA Applications")
            launcher_icon = Gtk.Image.new_from_icon_name("view-app-grid-symbolic")
            launcher_icon.set_pixel_size(32)
            launcher_btn.set_child(launcher_icon)
            launcher_btn.connect("clicked", lambda _b: self.logic.app_mgr.launch("laya-launcher"))
            dock_box.append(launcher_btn)

            # Laya AI Orb Trigger
            orb_btn = Gtk.Button()
            orb_btn.add_css_class("laya-dock-item")
            orb_btn.add_css_class("laya-ai-orb-idle")
            orb_btn.set_tooltip_text("Talk to Laya AI (Hey Laya)")
            orb_icon = Gtk.Image.new_from_icon_name("microphone-sensitivity-high-symbolic")
            orb_icon.set_pixel_size(32)
            orb_btn.set_child(orb_icon)

            def on_orb_click(_b):
                state = self.logic.activate_laya_orb()
                if state["laya_active"]:
                    orb_btn.remove_css_class("laya-ai-orb-idle")
                    orb_btn.add_css_class("laya-ai-orb-active")
                else:
                    orb_btn.remove_css_class("laya-ai-orb-active")
                    orb_btn.add_css_class("laya-ai-orb-idle")

            orb_btn.connect("clicked", on_orb_click)
            dock_box.append(orb_btn)

            # Pinned Apps
            for idx, app_info in enumerate(self.logic.pinned_apps):
                btn = Gtk.Button()
                btn.add_css_class("laya-dock-item")
                btn.set_tooltip_text(app_info["name"])
                icon = Gtk.Image.new_from_icon_name(app_info["icon"])
                icon.set_pixel_size(32)
                btn.set_child(icon)
                btn.connect("clicked", lambda _b, i=idx: self.logic.launch_pinned(i))
                dock_box.append(btn)

            win.present()


def main():
    if _GTK_AVAILABLE:
        app = LayaDockApp()
        sys.exit(app.run(sys.argv))
    else:
        dock = LayaDock()
        print(f"[LAYA OS Dock] Initialized with {len(dock.pinned_apps)} pinned applications.")


if __name__ == "__main__":
    main()
