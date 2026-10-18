import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = "database.db"
LEGACY_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "publication_history.db",
)


def _migrate_legacy_history(conn):
    if os.path.abspath(DB_PATH) != os.path.abspath("database.db"):
        return
    if not os.path.exists(LEGACY_DB_PATH):
        return

    legacy_conn = sqlite3.connect(LEGACY_DB_PATH)
    try:
        has_history = legacy_conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'history'"
        ).fetchone()
        if not has_history:
            return
        rows = legacy_conn.execute(
            """
            SELECT topic, video_type, title, youtube_id, privacy_status, created_at
            FROM history
            """
        ).fetchall()
    finally:
        legacy_conn.close()

    for topic, video_type, title, youtube_id, privacy, published_at in rows:
        already_recorded = conn.execute(
            """
            SELECT 1 FROM published_videos
            WHERE (youtube_id IS NOT NULL AND youtube_id = ?)
               OR (topic = ? AND video_type = ?)
            LIMIT 1
            """,
            (youtube_id, topic, video_type),
        ).fetchone()
        if not already_recorded:
            conn.execute(
                """
                INSERT INTO published_videos
                    (topic, video_type, title, youtube_id, privacy, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (topic, video_type, title, youtube_id, privacy, published_at),
            )


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
    _migrate_legacy_history(conn)
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
