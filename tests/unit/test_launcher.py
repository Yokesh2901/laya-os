"""
Unit tests for LAYA OS Application Launcher and Tamil phonetic matching.
"""

import pytest
from desktop.launcher.main import LayaLauncherWindow
from system.hardware.apps import ApplicationManager


@pytest.fixture
def mock_app_manager(tmp_path):
    """Creates an isolated temporary XDG application directory independent of the host OS."""
    desktop_entries = {
        "google-chrome.desktop": (
            "[Desktop Entry]\n"
            "Name=Google Chrome\n"
            "Exec=google-chrome %U\n"
            "Icon=google-chrome\n"
            "Categories=Network;WebBrowser;\n"
        ),
        "gnome-calculator.desktop": (
            "[Desktop Entry]\n"
            "Name=Calculator\n"
            "Exec=gnome-calculator\n"
            "Icon=accessories-calculator\n"
            "Categories=Utility;Calculator;\n"
        ),
        "gnome-terminal.desktop": (
            "[Desktop Entry]\n"
            "Name=Terminal\n"
            "Exec=gnome-terminal\n"
            "Icon=utilities-terminal\n"
            "Categories=System;TerminalEmulator;\n"
        ),
        "firefox.desktop": (
            "[Desktop Entry]\n"
            "Name=Firefox Web Browser\n"
            "Exec=firefox %u\n"
            "Icon=firefox\n"
            "Categories=Network;WebBrowser;\n"
        ),
        "nautilus.desktop": (
            "[Desktop Entry]\n"
            "Name=Files\n"
            "Exec=nautilus --new-window\n"
            "Icon=system-file-manager\n"
            "Categories=System;FileManager;\n"
        ),
        "laya-settings.desktop": (
            "[Desktop Entry]\n"
            "Name=LAYA OS Settings\n"
            "Exec=laya-settings\n"
            "Icon=laya-logo\n"
            "Categories=Settings;\n"
        ),
    }

    for filename, content in desktop_entries.items():
        (tmp_path / filename).write_text(content, encoding="utf-8")

    return ApplicationManager(app_dirs=[str(tmp_path)])


def test_app_manager_tamil_resolution(mock_app_manager):
    # Tamil query for chrome
    app = mock_app_manager.find_app("க்ரோம்")
    assert app is not None
    assert "chrome" in app["name"].lower() or "chrome" in app["exec"].lower()

    # Tamil query for calculator
    app_calc = mock_app_manager.find_app("கால்குலேட்டர்")
    assert app_calc is not None
    assert "calculator" in app_calc["name"].lower() or "calculator" in app_calc["exec"].lower()


def test_launcher_search_filter(mock_app_manager):
    launcher = LayaLauncherWindow(app_manager=mock_app_manager)
    results = launcher.search("terminal")
    assert len(results) > 0
    assert any("terminal" in r["name"].lower() for r in results)

    # Empty search returns full catalog
    all_res = launcher.search("")
    assert len(all_res) >= len(results)


@pytest.mark.parametrize(
    "query,expected_substring",
    [
        ("க்ரோம்", "chrome"),
        ("கால்குலேட்டர்", "calculator"),
        ("டெர்மினல்", "terminal"),
        ("பயர்பாக்ஸ்", "firefox"),
        ("செட்டிங்ஸ்", "settings"),
        ("Chrome", "chrome"),
        ("calculator", "calculator"),
        ("Terminal", "terminal"),
        ("Files", "files"),
    ],
)
def test_launcher_tamil_and_english_search_regression(mock_app_manager, query, expected_substring):
    launcher = LayaLauncherWindow(app_manager=mock_app_manager)
    results = launcher.search(query)
    assert len(results) > 0
    assert any(expected_substring in r["name"].lower() for r in results)


def test_launcher_unknown_query_returns_empty(mock_app_manager):
    launcher = LayaLauncherWindow(app_manager=mock_app_manager)
    assert launcher.search("nonexistent_app_xyz_123") == []
