"""
LAYA OS - System Core D-Bus Service & Action Dispatcher
Exports org.laya.SystemCore on the Linux Session D-Bus and provides allowlisted OS operations.
"""

import os
import sys
import json
import shutil
import signal
import subprocess
import logging
from typing import Dict, Any, Optional

from system.permissions.policy import SecurityPolicyEngine, ActionRiskLevel
from system.permissions.confirm_dialog import request_user_confirmation
from system.hardware.monitoring import SystemMonitor
from system.hardware.audio import AudioManager
from system.hardware.display import DisplayManager
from system.hardware.apps import ApplicationManager

logger = logging.getLogger("laya.systemcore")

try:
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
    _GIO_AVAILABLE = True
except (ImportError, ValueError):
    _GIO_AVAILABLE = False


DBUS_INTROSPECTION_XML = """
<node>
  <interface name="org.laya.SystemCore">
    <method name="ExecuteAction">
      <arg type="s" name="action_name" direction="in"/>
      <arg type="s" name="params_json" direction="in"/>
      <arg type="b" name="confirmed_by_user" direction="in"/>
      <arg type="s" name="result_json" direction="out"/>
    </method>
    <method name="GetSystemStats">
      <arg type="s" name="stats_json" direction="out"/>
    </method>
    <method name="ListApplications">
      <arg type="s" name="apps_json" direction="out"/>
    </method>
    <method name="Ping">
      <arg type="s" name="pong" direction="out"/>
    </method>
    <signal name="ActionExecuted">
      <arg type="s" name="action_name"/>
      <arg type="b" name="success"/>
      <arg type="s" name="message"/>
    </signal>
  </interface>
</node>
"""


class LayaSystemCore:
    """
    Central system dispatcher for LAYA OS.
    Runs as a real Session D-Bus daemon on Linux and can also be invoked in-process.
    """

    DBUS_NAME = "org.laya.SystemCore"
    DBUS_PATH = "/org/laya/SystemCore"
    DBUS_INTERFACE = "org.laya.SystemCore"

    def __init__(self, require_confirmation: bool = True, interactive_confirm: bool = False):
        self.policy = SecurityPolicyEngine(require_confirmation_for_sensitive=require_confirmation)
        self.interactive_confirm = interactive_confirm
        self.monitor = SystemMonitor()
        self.audio = AudioManager()
        self.display = DisplayManager()
        self.apps = ApplicationManager()
        self._dbus_connection = None

    def execute_action(
        self,
        action_name: str,
        params: Optional[Dict[str, Any]] = None,
        confirmed_by_user: bool = False,
    ) -> Dict[str, Any]:
        """
        Validates permission and executes an allowlisted action.
        If the action is SENSITIVE and not yet confirmed, optionally prompts the user interactively.
        """
        params = params or {}
        risk = self.policy.classify_action(action_name, params)

        if risk == ActionRiskLevel.SENSITIVE and not confirmed_by_user and self.interactive_confirm:
            confirmed_by_user = request_user_confirmation(
                action_name, json.dumps(params, ensure_ascii=False)
            )

        authorized, reason = self.policy.validate_and_authorize(action_name, params, confirmed_by_user)

        if not authorized:
            return {
                "success": False,
                "action": action_name,
                "error": "SECURITY_POLICY_VIOLATION",
                "message": reason,
                "risk": risk.value,
            }

        try:
            handler = getattr(self, f"_action_{action_name}", None)
            if not handler:
                return {
                    "success": False,
                    "action": action_name,
                    "error": "ACTION_NOT_IMPLEMENTED",
                    "message": f"Action handler for '{action_name}' is not implemented.",
                }

            result = handler(params)
            self._emit_signal(action_name, True, f"Action '{action_name}' completed.")
            return {
                "success": True,
                "action": action_name,
                "result": result,
                "message": f"Action '{action_name}' completed successfully.",
            }
        except Exception as e:
            logger.exception(f"Error executing action {action_name}: {e}")
            self._emit_signal(action_name, False, str(e))
            return {
                "success": False,
                "action": action_name,
                "error": "EXECUTION_ERROR",
                "message": str(e),
            }

    def _emit_signal(self, action_name: str, success: bool, message: str):
        """Emits ActionExecuted D-Bus signal if connected to Session Bus."""
        if self._dbus_connection is not None and _GIO_AVAILABLE:
            try:
                self._dbus_connection.emit_signal(
                    None,
                    self.DBUS_PATH,
                    self.DBUS_INTERFACE,
                    "ActionExecuted",
                    GLib.Variant("(sbs)", (action_name, success, message)),
                )
            except Exception as e:
                logger.debug(f"Failed to emit D-Bus signal: {e}")

    # --- Safe Action Handlers ---

    def _action_get_system_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.monitor.get_system_summary()

    def _action_get_audio_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.audio.get_volume()

    def _action_set_audio_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        vol = params.get("volume", 50)
        ok, msg = self.audio.set_volume(int(vol))
        return {"success": ok, "message": msg}

    def _action_set_audio_mute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        mute = params.get("muted", True)
        ok, msg = self.audio.set_mute(bool(mute))
        return {"success": ok, "message": msg}

    def _action_get_brightness(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.display.get_brightness()

    def _action_set_brightness(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pct = params.get("brightness", 70)
        ok, msg = self.display.set_brightness(int(pct))
        return {"success": ok, "message": msg}

    def _action_list_applications(self, params: Dict[str, Any]) -> Dict[str, Any]:
        force = bool(params.get("force_refresh", False))
        apps = self.apps.scan_applications(force_refresh=force)
        return {"count": len(apps), "applications": apps}

    def _action_launch_application(self, params: Dict[str, Any]) -> Dict[str, Any]:
        app_name = params.get("name") or params.get("app") or ""
        ok, msg = self.apps.launch(app_name)
        return {"success": ok, "message": msg}

    def _action_search_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = str(params.get("query", "")).lower().strip()
        search_root = os.path.expanduser("~")
        max_results = min(int(params.get("limit", 20)), 100)

        matches = []
        if query:
            # Prefer fast fd-find on Linux if installed
            fd_bin = shutil.which("fdfind") or shutil.which("fd")
            if fd_bin:
                try:
                    out = subprocess.check_output(
                        [fd_bin, "--max-results", str(max_results), "-i", query, search_root],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=5,
                    )
                    matches = [line.strip() for line in out.splitlines() if line.strip()]
                    return {"query": query, "count": len(matches), "files": matches}
                except Exception:
                    pass

            for root, dirs, files in os.walk(search_root):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    if query in f.lower():
                        matches.append(os.path.join(root, f))
                        if len(matches) >= max_results:
                            break
                if len(matches) >= max_results:
                    break

        return {"query": query, "count": len(matches), "files": matches}

    def _action_get_active_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Query GNOME Shell / Mutter via D-Bus or xdotool fallback
        gdbus = shutil.which("gdbus")
        if gdbus:
            try:
                out = subprocess.check_output(
                    [
                        gdbus, "call", "--session",
                        "--dest", "org.gnome.Shell",
                        "--object-path", "/org/gnome/Shell",
                        "--method", "org.gnome.Shell.Eval",
                        "global.display.focus_window ? global.display.focus_window.get_title() : ''",
                    ],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=2,
                ).strip()
                return {"window_title": out, "backend": "gnome-shell"}
            except Exception:
                pass
        return {"window_title": "", "backend": "unavailable"}

    def _action_close_active_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        xdotool = shutil.which("xdotool")
        if xdotool:
            subprocess.Popen([xdotool, "getactivewindow", "windowclose"])
            return {"closed": True, "backend": "xdotool"}
        return {"closed": False, "backend": "wayland-restricted"}

    # --- Sensitive Action Handlers (Require Confirmation) ---

    def _action_system_poweroff(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if shutil.which("systemctl") and not params.get("dry_run"):
            subprocess.Popen(["systemctl", "poweroff"])
        return {"command": "systemctl poweroff", "status": "dispatched"}

    def _action_system_reboot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if shutil.which("systemctl") and not params.get("dry_run"):
            subprocess.Popen(["systemctl", "reboot"])
        return {"command": "systemctl reboot", "status": "dispatched"}

    def _action_system_lock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if shutil.which("loginctl") and not params.get("dry_run"):
            subprocess.Popen(["loginctl", "lock-session"])
        return {"command": "loginctl lock-session", "status": "dispatched"}

    def _action_system_suspend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if shutil.which("systemctl") and not params.get("dry_run"):
            subprocess.Popen(["systemctl", "suspend"])
        return {"command": "systemctl suspend", "status": "dispatched"}

    def _action_delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target = os.path.abspath(os.path.expanduser(str(params.get("path", ""))))
        home = os.path.abspath(os.path.expanduser("~"))
        if not target.startswith(home) or target == home:
            raise ValueError("Refusing to delete path outside user home directory.")
        if not os.path.exists(target):
            raise FileNotFoundError(f"Path not found: {target}")
        gio_bin = shutil.which("gio")
        if gio_bin and not params.get("dry_run"):
            subprocess.check_call([gio_bin, "trash", target])
            return {"trashed": target, "method": "gio-trash"}
        return {"trashed": target, "method": "dry-run"}

    def _action_kill_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pid = int(params.get("pid", 0))
        if pid <= 1:
            raise ValueError("Refusing to terminate PID <= 1.")
        if not params.get("dry_run"):
            os.kill(pid, signal.SIGTERM)
        return {"pid": pid, "signal": "SIGTERM"}

    # --- D-Bus Server Loop ---

    def run_dbus_daemon(self):
        """Registers org.laya.SystemCore on the Session D-Bus and runs GLib.MainLoop."""
        if not _GIO_AVAILABLE:
            logger.error("PyGObject (gi.repository.Gio) is required to run the D-Bus daemon.")
            sys.exit(1)

        node_info = Gio.DBusNodeInfo.new_for_xml(DBUS_INTROSPECTION_XML)
        interface_info = node_info.lookup_interface(self.DBUS_INTERFACE)

        def on_method_call(connection, sender, object_path, interface_name, method_name, parameters, invocation):
            try:
                if method_name == "Ping":
                    invocation.return_value(GLib.Variant("(s)", ("pong",)))
                elif method_name == "GetSystemStats":
                    res = self.execute_action("get_system_stats")
                    invocation.return_value(GLib.Variant("(s)", (json.dumps(res),)))
                elif method_name == "ListApplications":
                    res = self.execute_action("list_applications")
                    invocation.return_value(GLib.Variant("(s)", (json.dumps(res),)))
                elif method_name == "ExecuteAction":
                    action_name, params_json, confirmed = parameters.unpack()
                    params = json.loads(params_json) if params_json else {}
                    res = self.execute_action(action_name, params, confirmed_by_user=confirmed)
                    invocation.return_value(GLib.Variant("(s)", (json.dumps(res),)))
                else:
                    invocation.return_dbus_error(
                        "org.freedesktop.DBus.Error.UnknownMethod",
                        f"Unknown method: {method_name}",
                    )
            except Exception as e:
                invocation.return_dbus_error("org.laya.SystemCore.Error", str(e))

        def on_bus_acquired(connection, name):
            self._dbus_connection = connection
            connection.register_object(
                self.DBUS_PATH,
                interface_info,
                on_method_call,
                None,
                None,
            )
            logger.info(f"[D-Bus] Registered {self.DBUS_INTERFACE} at {self.DBUS_PATH}")

        def on_name_acquired(connection, name):
            logger.info(f"[D-Bus] Acquired bus name: {name}")

        def on_name_lost(connection, name):
            logger.warning(f"[D-Bus] Lost bus name: {name}")

        owner_id = Gio.bus_own_name(
            Gio.BusType.SESSION,
            self.DBUS_NAME,
            Gio.BusNameOwnerFlags.NONE,
            on_bus_acquired,
            on_name_acquired,
            on_name_lost,
        )

        loop = GLib.MainLoop()
        try:
            logger.info("[LAYA OS System Core] D-Bus daemon listening...")
            loop.run()
        except KeyboardInterrupt:
            logger.info("[LAYA OS System Core] Shutting down...")
        finally:
            Gio.bus_unown_name(owner_id)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    core = LayaSystemCore(interactive_confirm=True)
    if _GIO_AVAILABLE:
        core.run_dbus_daemon()
    else:
        print("[LAYA OS System Core] PyGObject/Gio unavailable; running in standalone mode.")


if __name__ == "__main__":
    main()
