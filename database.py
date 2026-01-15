import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instagram_username TEXT NOT NULL,
            telegram_user_id INTEGER,
            is_subscribed BOOLEAN DEFAULT 0,
            tracker_sent_at DATETIME,
            logs TEXT
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
