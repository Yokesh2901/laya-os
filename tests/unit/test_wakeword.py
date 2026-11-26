"""
Unit tests for LAYA OS Wake-Word and RMS audio processing.
"""

import pytest
from laya.voice.wakeword import WakeWordDetector


def test_wake_word_detection():
    detector = WakeWordDetector()

    detected, cmd = detector.contains_wake_word("Hey Laya open chrome")
    assert detected is True
    assert cmd == "open chrome"

    detected, cmd = detector.contains_wake_word("ஹே லயா volume increase pannu")
    assert detected is True
    assert cmd == "volume increase pannu"

    detected, cmd = detector.contains_wake_word("Laya, what is the weather?")
    assert detected is True
    assert "weather" in cmd

    detected, cmd = detector.contains_wake_word("Just chatting without any trigger")
    assert detected is False


def test_rms_calculation():
    detector = WakeWordDetector()

    # Empty bytes -> 0 RMS
    assert detector.calculate_rms(b"") == 0.0

    # Silent 16-bit audio (zeros) -> 0 RMS
    silent = b"\x00\x00" * 100
    assert detector.calculate_rms(silent) == 0.0

    # Non-zero audio
    audio_data = b"\x10\x00" * 100
    rms = detector.calculate_rms(audio_data)
    assert rms > 0.0
