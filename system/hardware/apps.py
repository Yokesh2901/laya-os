"""
LAYA OS - Application Management & XDG Indexer
Scans XDG .desktop files, resolves Tamil/Tanglish phonetic queries, and executes applications safely.
"""

import os
import glob
import subprocess
from typing import List, Dict, Any, Optional, Tuple


class ApplicationManager:
    """Discovers, parses, and launches Linux desktop applications."""

    # Tamil phonetic transliterations to application keywords
    TAMIL_APP_MAP: Dict[str, str] = {
        "க்ரோம்": "chrome",
        "கூகிள்": "chrome",
        "கூகுள்": "chrome",
        "பயர்பாக்ஸ்": "firefox",
        "பிரவுசர்": "browser",
        "இணையம்": "browser",
        "டெர்மினல்": "terminal",
        "கணினி": "terminal",
        "நோட்பேட்": "editor",
        "எழுத்து": "editor",
        "கால்குலேட்டர்": "calculator",
        "கணக்கீடு": "calculator",
        "செட்டிங்ஸ்": "settings",
        "அமைப்புகள்": "settings",
        "பைல்ஸ்": "files",
        "கோப்புகள்": "files",
        "மியூசிக்": "music",
        "பாட்டு": "music",
        "வீடியோ": "video",
        "கேமரா": "camera",
    }

    def __init__(self):
        self.app_dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications")
        ]
        self._cached_apps: List[Dict[str, Any]] = []

    def scan_applications(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Parses all installed .desktop files into a structured index."""
        if self._cached_apps and not force_refresh:
            return self._cached_apps

        apps: List[Dict[str, Any]] = []
        seen_names = set()

        for directory in self.app_dirs:
            if not os.path.isdir(directory):
                continue
            for filepath in glob.glob(os.path.join(directory, "*.desktop")):
                try:
                    app_info = self._parse_desktop_file(filepath)
                    if app_info and app_info["name"] not in seen_names:
                        seen_names.add(app_info["name"])
                        apps.append(app_info)
                except Exception:
                    continue

        # If running on host without full XDG desktop files, supply standard baseline apps
        if not apps:
            apps = [
                {"name": "Google Chrome", "exec": "google-chrome", "icon": "google-chrome", "categories": ["Network", "WebBrowser"]},
                {"name": "Firefox Web Browser", "exec": "firefox", "icon": "firefox", "categories": ["Network", "WebBrowser"]},
                {"name": "Terminal", "exec": "gnome-terminal", "icon": "utilities-terminal", "categories": ["System", "TerminalEmulator"]},
                {"name": "Text Editor", "exec": "gnome-text-editor", "icon": "accessories-text-editor", "categories": ["Utility", "TextEditor"]},
                {"name": "Files", "exec": "nautilus", "icon": "system-file-manager", "categories": ["System", "FileManager"]},
                {"name": "Calculator", "exec": "gnome-calculator", "icon": "accessories-calculator", "categories": ["Utility", "Calculator"]},
                {"name": "LAYA Settings", "exec": "laya-settings", "icon": "preferences-system", "categories": ["Settings"]},
            ]

        self._cached_apps = sorted(apps, key=lambda x: x["name"].lower())
        return self._cached_apps

    def _parse_desktop_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Extracts metadata from a single .desktop file."""
        name = ""
        exec_cmd = ""
        icon = ""
        no_display = False
        categories: List[str] = []

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            in_main_section = False
            for line in f:
                line = line.strip()
                if line == "[Desktop Entry]":
                    in_main_section = True
                    continue
                elif line.startswith("[") and in_main_section:
                    break  # exited [Desktop Entry]

                if in_main_section and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()

                    if key == "Name":
                        name = val
                    elif key == "Exec":
                        # Strip field codes like %U, %F
                        cleaned_exec = " ".join([p for p in val.split() if not p.startswith("%")])
                        exec_cmd = cleaned_exec
                    elif key == "Icon":
                        icon = val
                    elif key == "NoDisplay" and val.lower() == "true":
                        no_display = True
                    elif key == "Categories":
                        categories = [c.strip() for c in val.split(";") if c.strip()]

        if name and exec_cmd and not no_display:
            return {
                "name": name,
                "exec": exec_cmd,
                "icon": icon or "application-x-executable",
                "categories": categories,
                "filepath": filepath
            }
        return None

    def find_app(self, query: str) -> Optional[Dict[str, Any]]:
        """Finds the best matching application given an English, Tamil, or Tanglish query."""
        if not query:
            return None

        q_clean = query.strip().lower()

        # Check Tamil phonetic dictionary
        for tamil_token, eng_keyword in self.TAMIL_APP_MAP.items():
            if tamil_token in q_clean:
                q_clean = eng_keyword
                break

        apps = self.scan_applications()

        # Exact match
        for app in apps:
            if app["name"].lower() == q_clean:
                return app

        # Prefix / substring match on Name
        for app in apps:
            if q_clean in app["name"].lower():
                return app

        # Match on Exec or Category
        for app in apps:
            if q_clean in app["exec"].lower() or any(q_clean in c.lower() for c in app.get("categories", [])):
                return app

        return None

    def launch(self, query_or_exec: str) -> Tuple[bool, str]:
        """Launches an application without shell expansion."""
        app = self.find_app(query_or_exec)
        cmd = app["exec"] if app else query_or_exec

        # Safe tokenization without shell=True
        tokens = cmd.split()
        if not tokens:
            return False, "Empty launch command."

        try:
            # Spawn in background as a detached process
            subprocess.Popen(tokens, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            app_label = app["name"] if app else tokens[0]
            return True, f"Successfully launched {app_label}."
        except Exception as e:
            return False, f"Failed to launch {tokens[0]}: {str(e)}"
