import sqlite3
import os
from datetime import datetime

DB_PATH = "data/publication_history.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT UNIQUE,
        video_type TEXT,
        title TEXT,
        youtube_id TEXT,
        privacy_status TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def is_topic_used(topic: str) -> bool:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM history WHERE LOWER(topic) = LOWER(?)", (topic.strip(),))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_past_topics(limit: int = 50) -> list:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT topic FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def record_publication(topic: str, video_type: str, title: str, youtube_id: str, privacy: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO history (topic, video_type, title, youtube_id, privacy_status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (topic.strip(), video_type, title, youtube_id, privacy, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
