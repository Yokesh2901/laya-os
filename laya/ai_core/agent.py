"""
LAYA OS - Conversational Agent & Dialog Manager
Coordinates user voice/text queries, hierarchical intent resolution, OS actions, and spoken feedback.
"""

import re
import datetime
import logging
from typing import Dict, Any, Optional, Union

from system.dbus.service import LayaSystemCore
from system.dbus.client import SystemCoreClient
from laya.ai_core.llm import LLMAdapter
from laya.memory.store import PersistentMemoryStore
from laya.tts.engine import TextToSpeechEngine

logger = logging.getLogger("laya.agent")


class LayaAgent:
    """Central conversational and action execution agent for LAYA OS."""

    def __init__(
        self,
        system_core: Optional[Union[LayaSystemCore, SystemCoreClient]] = None,
        memory_store: Optional[PersistentMemoryStore] = None,
    ):
        self.sys = system_core or SystemCoreClient()
        self.memory = memory_store or PersistentMemoryStore()
        self.llm = LLMAdapter()
        self.tts = TextToSpeechEngine()

    def process_input(self, user_text: str, user_name: str = "Yokesh") -> Dict[str, Any]:
        """
        Main entry point for user requests.
        Handles fast direct deterministic intents first; routes ambiguous or open-ended queries to LLM.
        """
        if not user_text or not user_text.strip():
            return {"reply": "", "action": None, "spoken": False}

        raw = user_text.strip()
        lowered = raw.lower()

        # 1. Quick Clock / Time Intent
        if any(w in lowered for w in ["time enna", "what time", "மணி என்ன", "நேரம் என்ன", "time please"]):
            now = datetime.datetime.now().strftime("%I:%M %p")
            reply = f"இப்போ மணி {now}."
            self.memory.save_turn(raw, reply, action_executed="get_time")
            return {"reply": reply, "action": "get_time", "result": now}

        # 2. System Status / Telemetry Intent
        if any(w in lowered for w in ["system status", "battery", "cpu", "ram", "ஸ்டேட்டஸ்", "சிபியூ"]):
            stats = self.sys.execute_action("get_system_stats")
            cpu = stats.get("result", {}).get("cpu_percent", 0)
            mem_pct = stats.get("result", {}).get("memory", {}).get("percent", 0)
            reply = f"System normal-ஆ இருக்கு. CPU {cpu}%, RAM {mem_pct}% used."
            self.memory.save_turn(raw, reply, action_executed="get_system_stats")
            return {"reply": reply, "action": "get_system_stats", "result": stats.get("result")}

        # 3. Volume & Mute Control Intent
        if any(w in lowered for w in ["volume", "வால்யூம்", "சத்தம்", "mute", "மியூட்", "unmute", "அன்மியூட்"]):
            num_match = re.search(r"\b(\d{1,3})\b", lowered)
            if any(w in lowered for w in ["unmute", "அன்மியூட்"]):
                self.sys.execute_action("set_audio_mute", {"muted": False})
                reply = "அன்மியூட் பண்ணிட்டேன்."
                self.memory.save_turn(raw, reply, action_executed="set_audio_mute")
                return {"reply": reply, "action": "set_audio_mute"}
            elif any(w in lowered for w in ["mute", "மியூட்", "சைலன்ட்"]):
                self.sys.execute_action("set_audio_mute", {"muted": True})
                reply = "மியூட் பண்ணிட்டேன்."
                self.memory.save_turn(raw, reply, action_executed="set_audio_mute")
                return {"reply": reply, "action": "set_audio_mute"}
            elif num_match:
                vol = max(0, min(100, int(num_match.group(1))))
                self.sys.execute_action("set_audio_volume", {"volume": vol})
                reply = f"வால்யூம் {vol}%-க்கு செட் பண்ணிட்டேன்."
                self.memory.save_turn(raw, reply, action_executed="set_audio_volume")
                return {"reply": reply, "action": "set_audio_volume", "volume": vol}
            elif any(w in lowered for w in ["increase", "up", "அதிகம்", "ஏத்து"]):
                self.sys.execute_action("set_audio_volume", {"volume": 80})
                reply = "வால்யூம் அதிகப்படுத்திட்டேன்."
                self.memory.save_turn(raw, reply, action_executed="set_audio_volume")
                return {"reply": reply, "action": "set_audio_volume"}
            elif any(w in lowered for w in ["decrease", "down", "low", "குறை"]):
                self.sys.execute_action("set_audio_volume", {"volume": 35})
                reply = "வால்யூம் குறைச்சிட்டேன்."
                self.memory.save_turn(raw, reply, action_executed="set_audio_volume")
                return {"reply": reply, "action": "set_audio_volume"}

        # 4. Brightness Control Intent
        if "brightness" in lowered or "பிரைட்னஸ்" in lowered or "வெளிச்சம்" in lowered:
            num_match = re.search(r"\b(\d{1,3})\b", lowered)
            if num_match:
                pct = max(5, min(100, int(num_match.group(1))))
                self.sys.execute_action("set_brightness", {"brightness": pct})
                reply = f"பிரைட்னஸ் {pct}%-க்கு செட் பண்ணிட்டேன்."
                return {"reply": reply, "action": "set_brightness", "brightness": pct}
            elif any(w in lowered for w in ["increase", "up", "அதிகம்", "ஏத்து"]):
                self.sys.execute_action("set_brightness", {"brightness": 90})
                reply = "பிரைட்னஸ் அதிகப்படுத்திட்டேன்."
                return {"reply": reply, "action": "set_brightness"}
            elif any(w in lowered for w in ["decrease", "down", "low", "குறை"]):
                self.sys.execute_action("set_brightness", {"brightness": 40})
                reply = "பிரைட்னஸ் குறைச்சிட்டேன்."
                return {"reply": reply, "action": "set_brightness"}

        # 5. File Search Intent
        if any(w in lowered for w in ["search file", "find file", "பைல் தேடு", "கோப்பு தேடு"]):
            query = re.sub(r".*(search file|find file|பைல் தேடு|கோப்பு தேடு)\s*", "", lowered).strip()
            if query:
                res = self.sys.execute_action("search_files", {"query": query, "limit": 10})
                count = res.get("result", {}).get("count", 0)
                reply = f"'{query}'-க்கு {count} files கிடைச்சிருக்கு."
                self.memory.save_turn(raw, reply, action_executed="search_files")
                return {"reply": reply, "action": "search_files", "result": res.get("result")}

        # 6. Sensitive Power / Lock Actions (Governed by SecurityPolicyEngine)
        if any(w in lowered for w in ["lock screen", "system lock", "லாக் பண்ணு"]):
            res = self.sys.execute_action("system_lock")
            if res.get("success"):
                reply = "ஸ்கிரீன் லாக் பண்ணிட்டேன்."
                return {"reply": reply, "action": "system_lock"}
            reply = "ஸ்கிரீன் லாக் பண்ண confirmation தேவை."
            return {"reply": reply, "action": "system_lock", "requires_confirmation": True}

        # 7. Application Launching Intent
        if any(w in lowered for w in ["open", "launch", "start", "ஓபன்", "துவங்கு"]):
            target = re.sub(r"^(open|launch|start|please open|தயவுசெய்து|ஓபன் பண்ணு)\s*", "", lowered, flags=re.IGNORECASE).strip()
            if target:
                res = self.sys.execute_action("launch_application", {"app": target})
                if res.get("success"):
                    reply = f"{target} ஓபன் பண்ணிட்டேன்."
                    self.memory.save_turn(raw, reply, action_executed=f"launch_{target}")
                    return {"reply": reply, "action": "launch_application", "target": target}

        # 8. Conversational / General Knowledge QA (Route to LLM)
        llm_res = self.llm.generate_reply(prompt=raw)
        reply = llm_res.get("reply", "சரிங்க, நான் உங்களுக்கு உதவ தயாரா இருக்கேன்.")
        self.memory.save_turn(raw, reply, action_executed="llm_dialogue")
        return {"reply": reply, "action": "llm_chat", "model": llm_res.get("model")}
