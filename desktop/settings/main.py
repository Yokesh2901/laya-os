"""
LAYA OS - System Settings Application
Manages AI preferences, voice models, language selection, audio/display, and telemetry.
"""

import sys
from typing import Dict, Any, Optional

from system.dbus.service import LayaSystemCore
from laya.memory.store import PersistentMemoryStore
from desktop.theme.loader import apply_laya_theme

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Adw
    _GTK_AVAILABLE = True
except (ImportError, ValueError):
    _GTK_AVAILABLE = False


class LayaSettingsManager:
    """Manages system and AI configuration parameters for LAYA OS."""

    def __init__(
        self,
        system_core: Optional[LayaSystemCore] = None,
        memory_store: Optional[PersistentMemoryStore] = None,
    ):
        self.sys = system_core or LayaSystemCore()
        self.memory = memory_store or PersistentMemoryStore()

    def get_all_settings(self) -> Dict[str, Any]:
        """Retrieves active configuration profile."""
        return {
            "ai": {
                "provider": self.memory.get_preference("ai_provider", "ollama"),
                "model": self.memory.get_preference("ai_model", "phi3:latest"),
                "language": self.memory.get_preference("language", "ta-IN"),
                "voice_preference": self.memory.get_preference("voice", "Indian Female (Aarti/Pallavi)"),
                "stt_engine": self.memory.get_preference("stt_engine", "local"),
                "tts_engine": self.memory.get_preference("tts_engine", "local"),
            },
            "system": {
                "volume": self.sys.audio.get_volume(),
                "brightness": self.sys.display.get_brightness(),
                "stats": self.sys.monitor.get_system_summary(),
            },
        }

    def update_ai_setting(self, key: str, value: Any):
        """Updates an AI configuration parameter."""
        self.memory.set_preference(key, value)
        return {"status": "updated", "key": key, "value": value}


if _GTK_AVAILABLE:
    class LayaSettingsApp(Adw.Application):
        """Libadwaita Preferences Window for LAYA OS."""

        def __init__(self):
            super().__init__(application_id="org.laya.Settings")
            self.mgr = LayaSettingsManager()
            self.connect("activate", self.on_activate)

        def on_activate(self, app):
            apply_laya_theme()
            settings = self.mgr.get_all_settings()

            win = Adw.PreferencesWindow(application=app)
            win.set_title("LAYA OS Settings")
            win.set_default_size(680, 520)

            # Page 1: Laya AI Core
            ai_page = Adw.PreferencesPage(title="Laya AI", icon_name="audio-input-microphone-symbolic")
            win.add(ai_page)

            ai_group = Adw.PreferencesGroup(
                title="Intelligence & Voice",
                description="Configure local LLM, speech recognition, and Indian female voice synthesis.",
            )
            ai_page.add(ai_group)

            lang_row = Adw.ActionRow(title="Primary Language", subtitle="Tamil, English, and Tanglish Code-Mix")
            lang_combo = Gtk.ComboBoxText()
            for code, label in [("ta-IN", "Tamil / Tanglish (ta-IN)"), ("en-IN", "Indian English (en-IN)")]:
                lang_combo.append(code, label)
            lang_combo.set_active_id(settings["ai"]["language"])
            lang_combo.connect(
                "changed",
                lambda c: self.mgr.update_ai_setting("language", c.get_active_id()),
            )
            lang_row.add_suffix(lang_combo)
            ai_group.add(lang_row)

            model_row = Adw.ActionRow(title="Local LLM Model", subtitle=f"Provider: {settings['ai']['provider']}")
            model_entry = Gtk.Entry()
            model_entry.set_text(str(settings["ai"]["model"]))
            model_entry.connect(
                "activate",
                lambda e: self.mgr.update_ai_setting("ai_model", e.get_text().strip()),
            )
            model_row.add_suffix(model_entry)
            ai_group.add(model_row)

            # Page 2: System & Hardware
            sys_page = Adw.PreferencesPage(title="System", icon_name="preferences-system-symbolic")
            win.add(sys_page)

            hw_group = Adw.PreferencesGroup(title="Audio & Display")
            sys_page.add(hw_group)

            vol_row = Adw.ActionRow(title="Master Volume", subtitle="PipeWire Audio Sink")
            vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
            vol_scale.set_size_request(180, -1)
            vol_scale.set_value(settings["system"]["volume"].get("volume", 65))
            vol_scale.connect(
                "value-changed",
                lambda s: self.mgr.sys.execute_action("set_audio_volume", {"volume": int(s.get_value())}),
            )
            vol_row.add_suffix(vol_scale)
            hw_group.add(vol_row)

            bright_row = Adw.ActionRow(title="Display Brightness", subtitle="Backlight Controller")
            bright_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 100, 5)
            bright_scale.set_size_request(180, -1)
            bright_scale.set_value(settings["system"]["brightness"].get("brightness", 70))
            bright_scale.connect(
                "value-changed",
                lambda s: self.mgr.sys.execute_action("set_brightness", {"brightness": int(s.get_value())}),
            )
            bright_row.add_suffix(bright_scale)
            hw_group.add(bright_row)

            stats = settings["system"]["stats"]
            telemetry_group = Adw.PreferencesGroup(title="Hardware Telemetry")
            sys_page.add(telemetry_group)
            telemetry_group.add(
                Adw.ActionRow(
                    title="CPU & Memory",
                    subtitle=f"CPU: {stats.get('cpu_percent', 0)}% | RAM: {stats['memory'].get('percent', 0)}% ({stats['memory'].get('used_mb', 0)} / {stats['memory'].get('total_mb', 0)} MB)",
                )
            )
            telemetry_group.add(
                Adw.ActionRow(
                    title="Storage",
                    subtitle=f"Disk: {stats['disk'].get('used_gb', 0)} GB / {stats['disk'].get('total_gb', 0)} GB ({stats['disk'].get('percent', 0)}%)",
                )
            )

            win.present()


def main():
    if _GTK_AVAILABLE:
        app = LayaSettingsApp()
        sys.exit(app.run(sys.argv))
    else:
        mgr = LayaSettingsManager()
        settings = mgr.get_all_settings()
        print("[LAYA OS Settings] Loaded system settings successfully:")
        print(f"  AI Model: {settings['ai']['model']}")
        print(f"  Language: {settings['ai']['language']}")


if __name__ == "__main__":
    main()
