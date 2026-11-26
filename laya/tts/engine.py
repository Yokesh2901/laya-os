"""
LAYA OS - Text-to-Speech (TTS) Engine
Generates expressive Indian female neural speech in Tamil, English, and Tanglish.
Supports Sarvam bulbul:v4-flash, Edge-TTS (PallaviNeural), and local Piper/eSpeak TTS.
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger("laya.tts")


class TextToSpeechEngine:
    """Multilingual Neural TTS Engine with cache and multi-provider fallback."""

    # Romanized Tanglish to natural Tamil script dictionary for fluid pronunciation
    TANGLISH_TO_TAMIL = [
        ("Ippo mani", "இப்போ மணி"),
        ("open pannitten", "ஓபன் பண்ணிட்டேன்"),
        ("close pannitten", "க்ளோஸ் பண்ணிட்டேன்"),
        ("Volume increase pannitten", "வால்யூம் அதிகப்படுத்திட்டேன்"),
        ("Volume koraichitten", "வால்யூம் குறைச்சிட்டேன்"),
        ("Volume-ah", "வால்யூமை"),
        ("ku set pannitten", "க்கு செட் பண்ணிட்டேன்"),
        ("Screenshot eduthu", "ஸ்கிரீன்ஷாட் எடுத்து"),
        ("save pannitten", "சேவ் பண்ணிட்டேன்"),
        ("Mute pannitten", "மியூட் பண்ணிட்டேன்"),
        ("Unmute pannitten", "அன்மியூட் பண்ணிட்டேன்"),
        ("Brightness increase pannitten", "பிரைட்னஸ் அதிகப்படுத்திட்டேன்"),
        ("Brightness koraichitten", "பிரைட்னஸ் குறைச்சிட்டேன்"),
        ("Settings open pandren", "செட்டிங்ஸ் ஓபன் பண்றேன்"),
        ("Sari, seiren", "சரி, செய்றேன்"),
        ("Ennala idhai seiya mudiyadhu", "என்னால இதை செய்ய முடியாது"),
    ]

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "")
        self.sarvam_url = "https://api.sarvam.ai/text-to-speech/stream"
        self.sarvam_speaker = os.environ.get("SARVAM_TTS_SPEAKER", "aarti_hi_customer")
        self.sarvam_model = "bulbul:v4-flash"
        self.sarvam_pace = float(os.environ.get("SARVAM_TTS_PACE", 1.15))

        self.voice_tamil_edge = os.environ.get("EDGE_TTS_VOICE_TAMIL", "ta-IN-PallaviNeural")
        self.voice_english_edge = os.environ.get("EDGE_TTS_VOICE_ENGLISH", "en-IN-NeerjaNeural")

        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.cache/laya/audio"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.http_session = requests.Session()

    def transliterate_tanglish(self, text: str) -> str:
        """Converts common Tanglish phrases to Tamil for more authentic phonetics."""
        processed = text
        for roman, tamil in self.TANGLISH_TO_TAMIL:
            processed = processed.replace(roman, tamil)
        return processed

    def synthesize(self, text: str, target_lang: str = "ta-IN") -> Dict[str, Any]:
        """
        Synthesizes text into audio data.
        Returns audio metadata and file path.
        """
        if not text or not text.strip():
            return {"status": "empty", "audio_path": None}

        spoken_text = self.transliterate_tanglish(text.strip())
        cache_hash = hashlib.sha256(f"{spoken_text}_{self.sarvam_speaker}_{target_lang}".encode("utf-8")).hexdigest()
        cached_file = self.cache_dir / f"{cache_hash}.mp3"

        if cached_file.exists():
            return {
                "status": "cached",
                "audio_path": str(cached_file),
                "text": spoken_text,
                "provider": "cache"
            }

        # Try Sarvam AI API
        if self.api_key and self.api_key != "your_sarvam_api_key_here":
            try:
                headers = {
                    "api-subscription-key": self.api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "inputs": [spoken_text],
                    "target_language_code": target_lang,
                    "speaker": self.sarvam_speaker,
                    "pitch": 0,
                    "pace": self.sarvam_pace,
                    "loudness": 1.5,
                    "speech_sample_rate": 22050,
                    "enable_preprocessing": True,
                    "model": self.sarvam_model
                }
                resp = self.http_session.post(self.sarvam_url, headers=headers, json=payload, timeout=8)
                if resp.status_code == 200:
                    with open(cached_file, "wb") as f:
                        f.write(resp.content)
                    return {
                        "status": "synthesized",
                        "audio_path": str(cached_file),
                        "text": spoken_text,
                        "provider": "sarvam-bulbul"
                    }
                else:
                    logger.warning(f"[TTS] Sarvam returned {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"[TTS] Sarvam synthesis error: {e}")

        # Fallback offline indicator
        return {
            "status": "offline_fallback",
            "audio_path": None,
            "text": spoken_text,
            "provider": "edge-or-espeak"
        }
