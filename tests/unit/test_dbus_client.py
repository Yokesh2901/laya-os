"""
Unit tests for LAYA OS SystemCoreClient and D-Bus security enforcement.
"""

from system.dbus.client import SystemCoreClient


def test_dbus_client_ping_and_stats():
    client = SystemCoreClient(use_dbus=False)
    assert client.ping() is True

    res = client.execute_action("get_system_stats")
    assert res["success"] is True
    assert "cpu_percent" in res["result"]
    assert "memory" in res["result"]


def test_dbus_client_blocks_sensitive_without_confirmation():
    client = SystemCoreClient(use_dbus=False)
    res = client.execute_action("system_poweroff", {"dry_run": True}, confirmed_by_user=False)
    assert res["success"] is False
    assert res["error"] == "SECURITY_POLICY_VIOLATION"

    res_confirmed = client.execute_action("system_poweroff", {"dry_run": True}, confirmed_by_user=True)
    assert res_confirmed["success"] is True
    assert res_confirmed["result"]["command"] == "systemctl poweroff"


def test_dbus_client_blocks_forbidden_file_delete_outside_home():
    client = SystemCoreClient(use_dbus=False)
    res = client.execute_action("delete_file", {"path": "/etc/passwd", "dry_run": True}, confirmed_by_user=True)
    assert res["success"] is False
    assert res["error"] == "EXECUTION_ERROR"
