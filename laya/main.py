"""
LAYA OS - AI Core Service Daemon
Main runner coordinating Wake-Word detection, STT transcription, dialog management, and TTS output.
"""

import os
import sys
import time
import logging
from typing import Optional

from laya.voice.wakeword import WakeWordDetector
from laya.stt.engine import SpeechToTextEngine
from laya.tts.engine import TextToSpeechEngine
from laya.ai_core.agent import LayaAgent
from system.dbus.service import LayaSystemCore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("laya.daemon")


class LayaCoreDaemon:
    """Orchestrates the voice listening loop and conversational interactions."""

    def __init__(self):
        logger.info("Initializing LAYA OS Core Daemon...")
        self.sys_core = LayaSystemCore()
        self.agent = LayaAgent(system_core=self.sys_core)
        self.wakeword = WakeWordDetector()
        self.stt = SpeechToTextEngine()
        self.tts = TextToSpeechEngine()
        self._running = False

    def start(self):
        """Starts the daemon."""
        self._running = True
        logger.info("LAYA AI Core Daemon running. Listening for 'Hey Laya' wake-word...")
        try:
            while self._running:
                time.sleep(1.0)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stops the daemon gracefully."""
        self._running = False
        logger.info("LAYA AI Core Daemon stopped.")


def main():
    daemon = LayaCoreDaemon()
    daemon.start()


if __name__ == "__main__":
    main()
