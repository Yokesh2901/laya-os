"""
LAYA OS - LLM Provider Adapter
Interfaces with local Ollama, Llama.cpp, and compatible LLM runtimes for intelligent dialogue.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List

import requests

logger = logging.getLogger("laya.llm")


class LLMAdapter:
    """Manages inference requests to local Small Language Models (SLMs) and cloud LLMs."""

    def __init__(self, provider: str = "ollama", host: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or os.environ.get("LAYA_LLM_PROVIDER", "ollama")
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "phi3:latest")
        self.http_session = requests.Session()

    def generate_reply(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Submits prompt to LLM and returns the structured answer.
        """
        full_system = (
            system_prompt or
            "You are LAYA, the intelligent, voice-first AI operating system assistant for LAYA OS. "
            "You speak natural Tamil, Indian English, and Tanglish. "
            "Always be super concise and direct (1-2 sentences max, zero fluff, straight to action). "
            "Address the user with warmth and efficiency."
        )

        if self.provider == "ollama":
            url = f"{self.host.rstrip('/')}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": full_system,
                "stream": False,
                "options": {
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "num_predict": 128
                }
            }
            try:
                resp = self.http_session.post(url, json=payload, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get("response", "").strip()
                    return {"reply": reply, "model": self.model, "provider": "ollama", "status": "ok"}
                else:
                    logger.warning(f"[LLM] Ollama returned status {resp.status_code}")
            except Exception as e:
                logger.info(f"[LLM] Ollama offline or unreachable ({e}). Using fast deterministic response.")

        # Fast deterministic fallback when offline
        return {
            "reply": "சரிங்க, நான் உங்களுக்கு உதவ தயாரா இருக்கேன்.",
            "model": "offline-rule",
            "provider": "offline",
            "status": "offline_fallback"
        }
