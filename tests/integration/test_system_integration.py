"""
Integration tests for LAYA OS end-to-end action execution and memory persistence.
"""

import pytest
from system.dbus.service import LayaSystemCore
from laya.ai_core.agent import LayaAgent
from laya.memory.store import PersistentMemoryStore


def test_end_to_end_query_execution(tmp_path):
    db_file = str(tmp_path / "integration_memory.db")
    memory = PersistentMemoryStore(db_path=db_file)
    sys_core = LayaSystemCore()
    agent = LayaAgent(system_core=sys_core, memory_store=memory)

    # 1. Ask for system status
    res = agent.process_input("system status check pannu")
    assert res["action"] == "get_system_stats"
    assert "CPU" in res["reply"]

    # 2. Verify turn was persisted to SQLite memory
    turns = memory.get_recent_turns(limit=5)
    assert len(turns) == 1
    assert "system status check pannu" in turns[0]["user_text"]
    assert turns[0]["action"] == "get_system_stats"

    # 3. Direct D-Bus system action test: audio volume query
    vol_res = sys_core.execute_action("get_audio_volume")
    assert vol_res["success"] is True
    assert "volume" in vol_res["result"]

    # 4. Direct D-Bus system action test: brightness query
    bright_res = sys_core.execute_action("get_brightness")
    assert bright_res["success"] is True
    assert "brightness" in bright_res["result"]
