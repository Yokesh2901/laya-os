"""
Unit tests for LAYA OS Conversational Agent and Intent Resolution.
"""

import pytest
from laya.ai_core.agent import LayaAgent
from system.dbus.service import LayaSystemCore
from laya.memory.store import PersistentMemoryStore


def test_agent_time_intent(tmp_path):
    db_file = str(tmp_path / "test_memory.db")
    memory = PersistentMemoryStore(db_path=db_file)
    agent = LayaAgent(memory_store=memory)

    res = agent.process_input("time enna")
    assert "மணி" in res["reply"]
    assert res["action"] == "get_time"

    res_tamil = agent.process_input("நேரம் என்ன")
    assert "மணி" in res_tamil["reply"]


def test_agent_system_status(tmp_path):
    db_file = str(tmp_path / "test_memory.db")
    memory = PersistentMemoryStore(db_path=db_file)
    agent = LayaAgent(memory_store=memory)

    res = agent.process_input("system status sollu")
    assert "CPU" in res["reply"]
    assert res["action"] == "get_system_stats"


def test_agent_volume_intent(tmp_path):
    db_file = str(tmp_path / "test_memory.db")
    memory = PersistentMemoryStore(db_path=db_file)
    agent = LayaAgent(memory_store=memory)

    res = agent.process_input("volume increase pannu")
    assert "அதிகப்படுத்திட்டேன்" in res["reply"]
    assert res["action"] == "set_audio_volume"

    res_mute = agent.process_input("mute pannu")
    assert "மியூட்" in res_mute["reply"]
