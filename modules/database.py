import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = "database.db"

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS published_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            video_type TEXT,
            title TEXT,
            youtube_id TEXT,
            privacy TEXT,
            published_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_past_topics(video_type: str = "short", limit: int = 50) -> list:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT topic FROM published_videos WHERE video_type = ? ORDER BY id DESC LIMIT ?",
        (video_type, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def is_topic_used(topic: str, video_type: str = "short") -> bool:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM published_videos WHERE topic = ? AND video_type = ?",
        (topic.strip(), video_type)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def is_duplicate(topic: str, video_type: str = "short") -> bool:
    return is_topic_used(topic, video_type)

def record_publication(topic: str, video_type: str, title: str, youtube_id: str, privacy: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO published_videos (topic, video_type, title, youtube_id, privacy, published_at) VALUES (?, ?, ?, ?, ?, ?)",
        (topic.strip(), video_type, title, youtube_id, privacy, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

def log_published_video(topic: str, video_type: str, title: str, youtube_id: str, privacy: str):
    record_publication(topic, video_type, title, youtube_id, privacy)
