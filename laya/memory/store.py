"""
LAYA OS - Persistent Memory Engine
SQLite-backed local storage for user preferences, entity memory, and interaction history.
"""

import os
import sqlite3
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path


class PersistentMemoryStore:
    """Manages long-term conversational memory and system personalization."""

    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            base_dir = Path(os.path.expanduser("~/.local/share/laya"))
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "memory.db")
        else:
            self.db_path = db_path

        self._init_database()

    def _init_database(self):
        """Initializes tables for turns, entities, and settings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    user_text TEXT,
                    laya_reply TEXT,
                    language TEXT,
                    action_executed TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at REAL
                )
            """)
            conn.commit()

    def save_turn(self, user_text: str, laya_reply: str, language: str = "ta-IN", action_executed: str = ""):
        """Stores a completed user-assistant interaction turn."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_history (timestamp, user_text, laya_reply, language, action_executed)
                VALUES (?, ?, ?, ?, ?)
            """, (time.time(), user_text, laya_reply, language, action_executed))
            conn.commit()

    def get_recent_turns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves recent conversation history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, user_text, laya_reply, language, action_executed
                FROM conversation_history
                ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()

        turns = []
        for r in reversed(rows):
            turns.append({
                "timestamp": r[0],
                "user_text": r[1],
                "laya_reply": r[2],
                "language": r[3],
                "action": r[4]
            })
        return turns

    def set_preference(self, key: str, value: Any):
        """Sets a user preference key/value."""
        val_str = json.dumps(value)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """, (key, val_str, time.time()))
            conn.commit()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Gets a user preference value."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return row[0]
        return default
