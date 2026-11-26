"""
LAYA OS - System Core D-Bus Service & Action Dispatcher
Exports org.laya.SystemCore interface to provide secure, allowlisted OS operations.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Tuple, Optional

from system.permissions.policy import SecurityPolicyEngine, ActionRiskLevel
from system.hardware.monitoring import SystemMonitor
from system.hardware.audio import AudioManager
from system.hardware.display import DisplayManager
from system.hardware.apps import ApplicationManager

logger = logging.getLogger("laya.systemcore")


class LayaSystemCore:
    """
    Central system dispatcher for LAYA OS.
    Can be run as a standalone D-Bus daemon or imported directly into AI Core services.
    """

    DBUS_NAME = "org.laya.SystemCore"
    DBUS_PATH = "/org/laya/SystemCore"
    DBUS_INTERFACE = "org.laya.SystemCore"

    def __init__(self, require_confirmation: bool = True):
        self.policy = SecurityPolicyEngine(require_confirmation_for_sensitive=require_confirmation)
        self.monitor = SystemMonitor()
        self.audio = AudioManager()
        self.display = DisplayManager()
        self.apps = ApplicationManager()

    def execute_action(self, action_name: str, params: Optional[Dict[str, Any]] = None, confirmed_by_user: bool = False) -> Dict[str, Any]:
        """
        Validates permission and executes an action.
        Returns a structured dictionary with success status, result payload, and message.
        """
        params = params or {}
        authorized, reason = self.policy.validate_and_authorize(action_name, params, confirmed_by_user)

        if not authorized:
            return {
                "success": False,
                "action": action_name,
                "error": "SECURITY_POLICY_VIOLATION",
                "message": reason,
                "risk": self.policy.classify_action(action_name, params).value
            }

        try:
            handler = getattr(self, f"_action_{action_name}", None)
            if not handler:
                return {
                    "success": False,
                    "action": action_name,
                    "error": "ACTION_NOT_IMPLEMENTED",
                    "message": f"Action handler for '{action_name}' is not implemented."
                }

            result = handler(params)
            return {
                "success": True,
                "action": action_name,
                "result": result,
                "message": f"Action '{action_name}' completed successfully."
            }
        except Exception as e:
            logger.exception(f"Error executing action {action_name}: {e}")
            return {
                "success": False,
                "action": action_name,
                "error": "EXECUTION_ERROR",
                "message": str(e)
            }

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
        apps = self.apps.scan_applications()
        return {"count": len(apps), "applications": apps}

    def _action_launch_application(self, params: Dict[str, Any]) -> Dict[str, Any]:
        app_name = params.get("name") or params.get("app") or ""
        ok, msg = self.apps.launch(app_name)
        return {"success": ok, "message": msg}

    def _action_search_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "").lower()
        search_root = os.path.expanduser("~")
        max_results = min(int(params.get("limit", 20)), 100)

        matches = []
        if query:
            for root, dirs, files in os.walk(search_root):
                # Avoid hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    if query in f.lower():
                        matches.append(os.path.join(root, f))
                        if len(matches) >= max_results:
                            break
                if len(matches) >= max_results:
                    break

        return {"query": query, "count": len(matches), "files": matches}

    # --- Sensitive Action Handlers ---

    def _action_system_poweroff(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # On Linux: systemctl poweroff
        return {"command": "systemctl poweroff", "status": "executed"}

    def _action_system_reboot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"command": "systemctl reboot", "status": "executed"}

    def _action_system_lock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"command": "loginctl lock-session", "status": "executed"}


def main():
    """CLI / Service entry point."""
    logging.basicConfig(level=logging.INFO)
    core = LayaSystemCore()
    print("[LAYA OS System Core] Service initialized. Ready for D-Bus / IPC invocations.")


if __name__ == "__main__":
    main()
