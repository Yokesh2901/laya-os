"""
LAYA OS - System Settings Application
Manages AI preferences, voice models, language selection, audio/display, and telemetry.
"""

import sys
import os
from typing import Dict, Any, Optional

from system.dbus.service import LayaSystemCore
from laya.memory.store import PersistentMemoryStore


class LayaSettingsManager:
    """Manages system and AI configuration parameters for LAYA OS."""

    def __init__(self, system_core: Optional[LayaSystemCore] = None, memory_store: Optional[PersistentMemoryStore] = None):
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
                "tts_engine": self.memory.get_preference("tts_engine", "local")
            },
            "system": {
                "volume": self.sys.audio.get_volume(),
                "brightness": self.sys.display.get_brightness(),
                "stats": self.sys.monitor.get_system_summary()
            }
        }

    def update_ai_setting(self, key: str, value: Any):
        """Updates an AI configuration parameter."""
        self.memory.set_preference(key, value)
        return {"status": "updated", "key": key, "value": value}


def main():
    mgr = LayaSettingsManager()
    settings = mgr.get_all_settings()
    print("[LAYA OS Settings] Loaded system settings successfully:")
    print(f"  AI Model: {settings['ai']['model']}")
    print(f"  Language: {settings['ai']['language']}")


if __name__ == "__main__":
    main()
