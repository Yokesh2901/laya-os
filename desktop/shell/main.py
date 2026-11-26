"""
LAYA OS - Desktop Shell Coordinator
Provides the LAYA Top Status Panel, 3D Particle Companion, Notification Overlay, and Quick Controls.
"""

import sys
import datetime
import logging

from system.dbus.client import SystemCoreClient
from desktop.launcher.main import LayaLauncherWindow
from desktop.dock.main import LayaDock
from desktop.widgets.particle_orb import ParticleSphereSimulator
from desktop.theme.loader import apply_laya_theme
from laya.ai_core.agent import LayaAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("laya.shell")

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Adw, GLib
    _GTK_AVAILABLE = True
except (ImportError, ValueError):
    _GTK_AVAILABLE = False


class LayaDesktopShell:
    """Master controller for the LAYA Desktop environment."""

    def __init__(self):
        logger.info("Initializing LAYA Desktop Shell...")
        self.sys_client = SystemCoreClient()
        self.dock = LayaDock()
        self.launcher = LayaLauncherWindow()
        self.orb_simulator = ParticleSphereSimulator(num_particles=800)
        self.is_running = False

    def toggle_launcher(self):
        """Opens the application launcher."""
        self.dock.app_mgr.launch("laya-launcher")

    def run(self):
        """Starts the desktop shell."""
        self.is_running = True
        if _GTK_AVAILABLE:
            app = LayaShellApp(self)
            return app.run(sys.argv)
        logger.info("LAYA Desktop Shell active (headless mode).")
        return 0


if _GTK_AVAILABLE:
    from desktop.widgets.particle_orb import create_gtk_orb_widget

    class LayaShellApp(Adw.Application):
        """GTK4/Libadwaita LAYA OS Desktop Shell Window."""

        def __init__(self, shell_ctrl: LayaDesktopShell):
            super().__init__(application_id="org.laya.DesktopShell")
            self.ctrl = shell_ctrl
            self.agent = LayaAgent(system_core=shell_ctrl.sys_client)
            self.connect("activate", self.on_activate)

        def on_activate(self, app):
            apply_laya_theme()

            win = Adw.ApplicationWindow(application=app)
            win.set_title("LAYA OS Desktop")
            win.set_default_size(1100, 700)
            win.add_css_class("laya-window")

            toast_overlay = Adw.ToastOverlay()
            win.set_content(toast_overlay)

            main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            toast_overlay.set_child(main_vbox)

            # --- Top Status Panel ---
            top_panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            top_panel.add_css_class("laya-top-panel")
            main_vbox.append(top_panel)

            apps_btn = Gtk.Button(label="LAYA Apps")
            apps_btn.add_css_class("laya-panel-pill")
            apps_btn.connect("clicked", lambda _b: self.ctrl.toggle_launcher())
            top_panel.append(apps_btn)

            laya_status_pill = Gtk.Label(label="● Laya AI Ready")
            laya_status_pill.add_css_class("laya-panel-pill")
            top_panel.append(laya_status_pill)

            spacer_left = Gtk.Box()
            spacer_left.set_hexpand(True)
            top_panel.append(spacer_left)

            clock_lbl = Gtk.Label(label=datetime.datetime.now().strftime("%a %b %d  %I:%M %p"))
            clock_lbl.add_css_class("laya-panel-pill")
            top_panel.append(clock_lbl)

            spacer_right = Gtk.Box()
            spacer_right.set_hexpand(True)
            top_panel.append(spacer_right)

            telemetry_lbl = Gtk.Label(label="CPU 0% | RAM 0%")
            telemetry_lbl.add_css_class("laya-panel-pill")
            top_panel.append(telemetry_lbl)

            settings_btn = Gtk.Button.new_from_icon_name("preferences-system-symbolic")
            settings_btn.add_css_class("laya-panel-pill")
            settings_btn.set_tooltip_text("LAYA Settings")
            settings_btn.connect("clicked", lambda _b: self.ctrl.dock.app_mgr.launch("laya-settings"))
            top_panel.append(settings_btn)

            # --- Center Workspace: 3D Particle Orb + Command Prompt ---
            center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
            center_box.set_vexpand(True)
            center_box.set_valign(Gtk.Align.CENTER)
            center_box.set_halign(Gtk.Align.CENTER)
            main_vbox.append(center_box)

            orb_area, orb_sim = create_gtk_orb_widget(size=240, num_particles=600)
            center_box.append(orb_area)

            title_lbl = Gtk.Label(label="LAYA OS — Intelligence Within")
            title_lbl.set_markup("<span size='x-large' weight='bold' foreground='#F8FAFC'>LAYA OS</span>  <span foreground='#22D3EE'>Intelligence Within</span>")
            center_box.append(title_lbl)

            reply_lbl = Gtk.Label(label="Vanakkam! Ask me anything in Tamil, English, or Tanglish.")
            reply_lbl.add_css_class("laya-glass-card")
            reply_lbl.set_wrap(True)
            reply_lbl.set_max_width_chars(56)
            center_box.append(reply_lbl)

            prompt_entry = Gtk.Entry()
            prompt_entry.set_placeholder_text("Type a command (e.g. 'open terminal', 'volume 80', 'time enna')...")
            prompt_entry.add_css_class("laya-search-bar")
            prompt_entry.set_size_request(520, -1)

            def on_prompt_submit(entry):
                text = entry.get_text().strip()
                if not text:
                    return
                entry.set_text("")
                orb_sim.audio_energy = 260.0
                res = self.agent.process_input(text)
                reply = res.get("reply", "")
                reply_lbl.set_text(reply)
                toast_overlay.add_toast(Adw.Toast.new(f"Action: {res.get('action', 'chat')}"))
                GLib.timeout_add(900, lambda: setattr(orb_sim, "audio_energy", 0.0) or False)

            prompt_entry.connect("activate", on_prompt_submit)
            center_box.append(prompt_entry)

            # --- Bottom Glassmorphic Dock ---
            dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            dock_box.add_css_class("laya-dock-container")
            dock_box.set_halign(Gtk.Align.CENTER)
            main_vbox.append(dock_box)

            for idx, app_info in enumerate(self.ctrl.dock.pinned_apps):
                btn = Gtk.Button()
                btn.add_css_class("laya-dock-item")
                btn.set_tooltip_text(app_info["name"])
                icon = Gtk.Image.new_from_icon_name(app_info["icon"])
                icon.set_pixel_size(32)
                btn.set_child(icon)
                btn.connect("clicked", lambda _b, i=idx: self.ctrl.dock.launch_pinned(i))
                dock_box.append(btn)

            # Live telemetry & clock timer
            def refresh_status():
                clock_lbl.set_text(datetime.datetime.now().strftime("%a %b %d  %I:%M %p"))
                stats_res = self.ctrl.sys_client.execute_action("get_system_stats")
                if stats_res.get("success"):
                    st = stats_res["result"]
                    cpu = st.get("cpu_percent", 0)
                    mem = st.get("memory", {}).get("percent", 0)
                    telemetry_lbl.set_text(f"CPU {cpu}% | RAM {mem}%")
                return True

            GLib.timeout_add_seconds(2, refresh_status)
            win.present()


def main():
    shell = LayaDesktopShell()
    sys.exit(shell.run())


if __name__ == "__main__":
    main()
