"""
LAYA OS - Wake-Word Detection & Voice Activity Detection (VAD)
Monitors 16kHz audio stream, calculates RMS audio energy, and triggers on wake words.
"""

import math
import struct
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger("laya.wakeword")


class WakeWordDetector:
    """Detects 'Hey Laya' wake-word activation and calculates audio loudness RMS."""

    WAKE_PHRASES: List[str] = [
        "hey laya",
        "laya",
        "ultra laya",
        "ஹே லயா",
        "லயா",
        "ok laya",
    ]

    def __init__(self, energy_threshold: float = 240.0):
        self.energy_threshold = energy_threshold
        self._is_listening = False

    @staticmethod
    def calculate_rms(pcm_data: bytes) -> float:
        """Calculates Root-Mean-Square amplitude of 16-bit PCM audio stream."""
        if not pcm_data:
            return 0.0

        count = len(pcm_data) // 2
        if count == 0:
            return 0.0

        format_str = f"<{count}h"
        try:
            shorts = struct.unpack(format_str, pcm_data)
            sum_squares = sum(s * s for s in shorts)
            return math.sqrt(sum_squares / count)
        except Exception:
            return 0.0

    def contains_wake_word(self, transcribed_text: str) -> Tuple[bool, str]:
        """
        Scans transcribed text for any known wake word.
        If found, strips the wake word and returns (True, command_text).
        """
        if not transcribed_text:
            return False, ""

        clean = transcribed_text.strip().lower()

        for wake in self.WAKE_PHRASES:
            if clean.startswith(wake):
                stripped = clean[len(wake):].strip(" ,.!?")
                return True, stripped
            elif wake in clean:
                parts = clean.split(wake, 1)
                stripped = parts[1].strip(" ,.!?") if len(parts) > 1 else ""
                return True, stripped

        return False, transcribed_text
