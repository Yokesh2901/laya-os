"""
LAYA OS - Interactive User Confirmation Dialog
Displays a GTK4/Libadwaita modal confirmation dialog for sensitive OS actions.
Falls back to zenity or CLI prompt if GTK4 is unavailable.
"""

import shutil
import subprocess
import logging
from typing import Optional

logger = logging.getLogger("laya.security.confirm")

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Adw, GLib
    _GTK_AVAILABLE = True
except (ImportError, ValueError):
    _GTK_AVAILABLE = False


def request_user_confirmation(action_name: str, description: str, timeout_sec: int = 30) -> bool:
    """
    Prompts the user to explicitly confirm a sensitive system action.
    Returns True only if the user clicks Confirm/Allow.
    """
    title = "LAYA OS Security Confirmation"
    body = f"Laya AI is requesting permission to execute a sensitive action:\n\nAction: {action_name}\nDetails: {description}\n\nDo you want to allow this?"

    # 1. Try zenity if available on Linux desktop (non-blocking to main loop, clean exit code)
    zenity_path = shutil.which("zenity")
    if zenity_path:
        try:
            proc = subprocess.run(
                [
                    zenity_path,
                    "--question",
                    f"--title={title}",
                    f"--text={body}",
                    "--ok-label=Allow",
                    "--cancel-label=Deny",
                    f"--timeout={timeout_sec}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout_sec + 5,
            )
            return proc.returncode == 0
        except Exception as e:
            logger.warning(f"Zenity confirmation failed: {e}")

    # 2. Try GTK4 Adw.MessageDialog if running in a GTK session
    if _GTK_AVAILABLE:
        result = {"confirmed": False}
        loop = GLib.MainLoop()

        def on_activate(app):
            win = Adw.ApplicationWindow(application=app)
            win.set_default_size(420, 200)
            win.set_title(title)

            dialog = Adw.MessageDialog(
                transient_for=win,
                heading=title,
                body=body,
            )
            dialog.add_response("deny", "Deny")
            dialog.add_response("allow", "Allow")
            dialog.set_response_appearance("allow", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("deny")
            dialog.set_close_response("deny")

            def on_response(_dlg, response_id):
                result["confirmed"] = (response_id == "allow")
                win.close()
                loop.quit()

            dialog.connect("response", on_response)
            dialog.present()

        app = Adw.Application(application_id="org.laya.SecurityConfirm")
        app.connect("activate", on_activate)
        GLib.timeout_add_seconds(timeout_sec, loop.quit)
        app.run(None)
        return result["confirmed"]

    logger.warning(f"No GUI confirmation backend available; denying sensitive action '{action_name}'.")
    return False
