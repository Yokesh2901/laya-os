"""
LAYA OS - System Core D-Bus Client
Connects to org.laya.SystemCore over Session D-Bus with seamless in-process fallback.
"""

import json
import logging
from typing import Dict, Any, Optional

from system.dbus.service import LayaSystemCore

logger = logging.getLogger("laya.dbus.client")

try:
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
    _GIO_AVAILABLE = True
except (ImportError, ValueError):
    _GIO_AVAILABLE = False


class SystemCoreClient:
    """Client interface to LayaSystemCore via D-Bus or in-process fallback."""

    def __init__(self, use_dbus: bool = True):
        self.use_dbus = use_dbus and _GIO_AVAILABLE
        self._proxy = None
        self._local_core: Optional[LayaSystemCore] = None

        if self.use_dbus:
            try:
                self._proxy = Gio.DBusProxy.new_for_bus_sync(
                    Gio.BusType.SESSION,
                    Gio.DBusProxyFlags.NONE,
                    None,
                    LayaSystemCore.DBUS_NAME,
                    LayaSystemCore.DBUS_PATH,
                    LayaSystemCore.DBUS_INTERFACE,
                    None,
                )
            except Exception as e:
                logger.info(f"[D-Bus Client] Session D-Bus unavailable ({e}); using local fallback.")
                self._proxy = None

    def _get_local_core(self) -> LayaSystemCore:
        if self._local_core is None:
            self._local_core = LayaSystemCore()
        return self._local_core

    def ping(self) -> bool:
        if self._proxy is not None:
            try:
                res = self._proxy.call_sync("Ping", None, Gio.DBusCallFlags.NONE, 2000, None)
                return res.unpack()[0] == "pong"
            except Exception:
                pass
        return True

    def execute_action(
        self,
        action_name: str,
        params: Optional[Dict[str, Any]] = None,
        confirmed_by_user: bool = False,
    ) -> Dict[str, Any]:
        params = params or {}
        if self._proxy is not None:
            try:
                args = GLib.Variant("(ssb)", (action_name, json.dumps(params), confirmed_by_user))
                res = self._proxy.call_sync("ExecuteAction", args, Gio.DBusCallFlags.NONE, 10000, None)
                return json.loads(res.unpack()[0])
            except Exception as e:
                logger.warning(f"[D-Bus Client] D-Bus call failed ({e}); falling back to local core.")

        return self._get_local_core().execute_action(action_name, params, confirmed_by_user)
