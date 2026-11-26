"""
Unit tests for LAYA OS Text-to-Speech Engine.
"""

from laya.tts.engine import TextToSpeechEngine


def test_tanglish_to_tamil_transliteration(tmp_path):
    tts = TextToSpeechEngine(cache_dir=str(tmp_path))
    converted = tts.transliterate_tanglish("Ippo mani 5 PM. Volume increase pannitten")
    assert "இப்போ மணி" in converted
    assert "வால்யூம் அதிகப்படுத்திட்டேன்" in converted


def test_tamil_script_detection():
    assert TextToSpeechEngine._has_tamil_script("வணக்கம்") is True
    assert TextToSpeechEngine._has_tamil_script("Hello world") is False
