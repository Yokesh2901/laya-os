"""
LAYA OS - Text-to-Speech (TTS) Engine
Generates expressive Indian female neural speech in Tamil, English, and Tanglish.
Supports Sarvam bulbul:v4-flash, Edge-TTS (PallaviNeural / NeerjaNeural), and local eSpeak-NG/Piper.
Plays audio through PipeWire (pw-play), PulseAudio (paplay), ffplay, or pygame.
"""

import os
import asyncio
import hashlib
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger("laya.tts")


class TextToSpeechEngine:
    """Multilingual Neural TTS Engine with cache, multi-provider fallback, and PipeWire playback."""

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
        self.is_speaking = False

    def transliterate_tanglish(self, text: str) -> str:
        """Converts common Tanglish phrases to Tamil for more authentic phonetics."""
        processed = text
        for roman, tamil in self.TANGLISH_TO_TAMIL:
            processed = processed.replace(roman, tamil)
        return processed

    @staticmethod
    def _has_tamil_script(text: str) -> bool:
        return any("\u0B80" <= ch <= "\u0BFF" for ch in text)

    def synthesize(self, text: str, target_lang: str = "ta-IN") -> Dict[str, Any]:
        """Synthesizes text into an audio file and returns metadata."""
        if not text or not text.strip():
            return {"status": "empty", "audio_path": None}

        spoken_text = self.transliterate_tanglish(text.strip())
        cache_hash = hashlib.sha256(f"{spoken_text}_{self.sarvam_speaker}_{target_lang}".encode("utf-8")).hexdigest()
        cached_file = self.cache_dir / f"{cache_hash}.mp3"

        if cached_file.exists() and cached_file.stat().st_size > 0:
            return {
                "status": "cached",
                "audio_path": str(cached_file),
                "text": spoken_text,
                "provider": "cache",
            }

        # 1. Try Sarvam AI API if configured
        if self.api_key and self.api_key != "your_sarvam_api_key_here":
            try:
                headers = {
                    "api-subscription-key": self.api_key,
                    "Content-Type": "application/json",
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
                    "model": self.sarvam_model,
                }
                resp = self.http_session.post(self.sarvam_url, headers=headers, json=payload, timeout=8)
                if resp.status_code == 200 and resp.content:
                    cached_file.write_bytes(resp.content)
                    return {
                        "status": "synthesized",
                        "audio_path": str(cached_file),
                        "text": spoken_text,
                        "provider": "sarvam-bulbul",
                    }
                logger.warning(f"[TTS] Sarvam returned {resp.status_code}")
            except Exception as e:
                logger.error(f"[TTS] Sarvam synthesis error: {e}")

        # 2. Try Edge-TTS (Indian female neural voice: Pallavi / Neerja)
        try:
            import edge_tts
            voice = self.voice_tamil_edge if self._has_tamil_script(spoken_text) else self.voice_english_edge

            async def _save_edge():
                communicate = edge_tts.Communicate(spoken_text, voice)
                await communicate.save(str(cached_file))

            asyncio.run(_save_edge())
            if cached_file.exists() and cached_file.stat().st_size > 0:
                return {
                    "status": "synthesized",
                    "audio_path": str(cached_file),
                    "text": spoken_text,
                    "provider": "edge-tts",
                }
        except Exception as e:
            logger.debug(f"[TTS] Edge-TTS unavailable: {e}")

        # 3. Local Offline Fallback (espeak-ng)
        return {
            "status": "offline_fallback",
            "audio_path": None,
            "text": spoken_text,
            "provider": "espeak-ng",
        }

    def speak(self, text: str, target_lang: str = "ta-IN") -> Dict[str, Any]:
        """Synthesizes and plays speech through PipeWire / PulseAudio / local TTS."""
        res = self.synthesize(text, target_lang=target_lang)
        audio_path = res.get("audio_path")

        self.is_speaking = True
        try:
            if audio_path and os.path.exists(audio_path):
                self._play_audio_file(audio_path)
            elif res.get("status") == "offline_fallback":
                espeak_bin = shutil.which("espeak-ng") or shutil.which("espeak")
                if espeak_bin:
                    lang_flag = "ta" if self._has_tamil_script(res["text"]) else "en-in"
                    subprocess.run([espeak_bin, "-v", lang_flag, res["text"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            self.is_speaking = False

        return res

    @staticmethod
    def _play_audio_file(filepath: str):
        """Plays an MP3/WAV file using available Linux audio players."""
        for player_cmd in (
            ["pw-play", filepath],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath],
            ["mpg123", "-q", filepath],
            ["paplay", filepath],
        ):
            if shutil.which(player_cmd[0]):
                try:
                    subprocess.run(player_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                    return
                except Exception:
                    continue
