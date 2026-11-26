"""
Unit tests for LAYA OS Application Launcher and Tamil phonetic matching.
"""

import pytest
from desktop.launcher.main import LayaLauncherWindow
from system.hardware.apps import ApplicationManager


def test_app_manager_tamil_resolution():
    app_mgr = ApplicationManager()

    # Tamil query for chrome
    app = app_mgr.find_app("க்ரோம்")
    assert app is not None
    assert "chrome" in app["name"].lower() or "chrome" in app["exec"].lower()

    # Tamil query for calculator
    app_calc = app_mgr.find_app("கால்குலேட்டர்")
    assert app_calc is not None
    assert "calculator" in app_calc["name"].lower() or "calculator" in app_calc["exec"].lower()


def test_launcher_search_filter():
    launcher = LayaLauncherWindow()
    results = launcher.search("terminal")
    assert len(results) > 0
    assert any("terminal" in r["name"].lower() for r in results)

    # Empty search returns full catalog
    all_res = launcher.search("")
    assert len(all_res) >= len(results)
