"""
LAYA OS - AI Core Service Daemon
Main runner coordinating Wake-Word detection, STT transcription, dialog management, and TTS output.
"""

import os
import sys
import time
import argparse
import logging
from typing import Optional

from laya.voice.wakeword import WakeWordDetector
from laya.stt.engine import SpeechToTextEngine
from laya.tts.engine import TextToSpeechEngine
from laya.ai_core.agent import LayaAgent
from system.dbus.client import SystemCoreClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("laya.daemon")


class LayaCoreDaemon:
    """Orchestrates the voice listening loop and conversational interactions."""

    def __init__(self):
        logger.info("Initializing LAYA OS Core Daemon...")
        self.sys_client = SystemCoreClient()
        self.agent = LayaAgent(system_core=self.sys_client)
        self.wakeword = WakeWordDetector()
        self.stt = SpeechToTextEngine()
        self.tts = TextToSpeechEngine()
        self._running = False

    def handle_utterance(self, transcript: str, speak_reply: bool = True) -> Optional[dict]:
        """Processes a transcribed utterance with wake-word filtering."""
        if not transcript or not transcript.strip():
            return None

        detected, command_text = self.wakeword.contains_wake_word(transcript)
        if not detected:
            logger.debug(f"Ignored non-wake utterance: {transcript}")
            return None

        query = command_text if command_text else "hello"
        logger.info(f"[Wake Triggered] Query: {query}")
        response = self.agent.process_input(query)
        reply = response.get("reply", "")
        if reply and speak_reply:
            self.tts.speak(reply)
        return response

    def run_voice_loop(self):
        """Captures microphone audio via SpeechRecognition/PyAudio and processes wake-word commands."""
        try:
            import speech_recognition as sr
        except ImportError:
            logger.warning("SpeechRecognition library not installed. Falling back to standby daemon.")
            self._run_standby_loop()
            return

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        try:
            mic = sr.Microphone(sample_rate=16000)
        except Exception as e:
            logger.warning(f"No audio capture device found ({e}). Running in standby mode.")
            self._run_standby_loop()
            return

        self._running = True
        logger.info("LAYA AI Core listening for 'Hey Laya' on microphone...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            while self._running:
                try:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=8)
                    wav_bytes = audio.get_wav_data()
                    pcm_bytes = audio.get_raw_data(convert_rate=16000, convert_width=2)
                    rms = self.wakeword.calculate_rms(pcm_bytes)
                    if rms < self.wakeword.energy_threshold:
                        continue

                    stt_res = self.stt.transcribe_audio_bytes(wav_bytes)
                    transcript = stt_res.get("text", "")
                    if transcript:
                        self.handle_utterance(transcript, speak_reply=True)
                except sr.WaitTimeoutError:
                    continue
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Voice loop error: {e}")
                    time.sleep(1.0)

        self.stop()

    def _run_standby_loop(self):
        """Standby loop when no microphone is attached (e.g. headless VM)."""
        self._running = True
        while self._running:
            try:
                time.sleep(2.0)
            except KeyboardInterrupt:
                break
        self.stop()

    def run_interactive_cli(self):
        """Runs an interactive text REPL for testing LAYA OS AI Core."""
        print("LAYA OS Interactive AI Shell (type 'exit' to quit)")
        while True:
            try:
                user_in = input("You > ").strip()
                if user_in.lower() in {"exit", "quit"}:
                    break
                res = self.agent.process_input(user_in)
                print(f"Laya > {res.get('reply', '')}")
            except (KeyboardInterrupt, EOFError):
                break

    def stop(self):
        self._running = False
        logger.info("LAYA AI Core Daemon stopped.")


def main():
    parser = argparse.ArgumentParser(description="LAYA OS AI Core Service")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive text CLI mode")
    args = parser.parse_args()

    daemon = LayaCoreDaemon()
    if args.interactive:
        daemon.run_interactive_cli()
    else:
        daemon.run_voice_loop()


if __name__ == "__main__":
    main()
