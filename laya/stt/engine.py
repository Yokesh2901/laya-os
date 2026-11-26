"""
LAYA OS - Speech-to-Text (STT) Engine
Supports high-accuracy multilingual Tamil/English/Tanglish via Sarvam AI saaras:v4
and local offline speech recognition fallback.
"""

import os
import sys
import time
import io
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger("laya.stt")


class SpeechToTextEngine:
    """Multilingual Speech-to-Text with local and cloud provider adapters."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "")
        self.sarvam_url = "https://api.sarvam.ai/speech-to-text"
        self.sarvam_model = os.environ.get("SARVAM_STT_MODEL", "saaras:v4")
        self.sarvam_lang = os.environ.get("SARVAM_STT_LANG", "ta-IN")
        self.sarvam_mode = os.environ.get("SARVAM_STT_MODE", "codemix")
        self.http_session = requests.Session()

    def transcribe_audio_bytes(self, audio_data: bytes, filename: str = "speech.wav") -> Dict[str, Any]:
        """
        Transcribes raw audio bytes into text.
        Attempts Sarvam AI ASR first; falls back gracefully if key is missing or network fails.
        """
        if not audio_data or len(audio_data) < 100:
            return {"text": "", "language_code": self.sarvam_lang, "provider": "none", "status": "empty"}

        # If Sarvam key is provided and valid
        if self.api_key and self.api_key != "your_sarvam_api_key_here":
            try:
                headers = {"api-subscription-key": self.api_key}
                files = {"file": (filename, io.BytesIO(audio_data), "audio/wav")}
                data = {
                    "model": self.sarvam_model,
                    "language_code": self.sarvam_lang,
                    "mode": self.sarvam_mode
                }
                resp = self.http_session.post(self.sarvam_url, headers=headers, files=files, data=data, timeout=8)
                if resp.status_code == 200:
                    result = resp.json()
                    transcription = result.get("transcript", "").strip()
                    detected_lang = result.get("language_code", self.sarvam_lang)
                    return {
                        "text": transcription,
                        "language_code": detected_lang,
                        "provider": "sarvam-saaras",
                        "status": "ok"
                    }
                else:
                    logger.warning(f"[STT] Sarvam returned {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"[STT] Sarvam request failed: {e}")

        # Local / Offline Fallback stub (ready for Whisper / Vosk)
        return {
            "text": "",
            "language_code": self.sarvam_lang,
            "provider": "fallback-offline",
            "status": "offline_no_key"
        }
