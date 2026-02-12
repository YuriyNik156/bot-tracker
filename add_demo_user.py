import sqlite3
from datetime import datetime

DB_PATH = "database.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO users (
        instagram_username,
        telegram_user_id,
        is_subscribed,
        tracker_sent_at,
        logs
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    (
        "demo_user",     # instagram_username
        None,            # telegram_user_id
        1,               # is_subscribed
        None,            # tracker_sent_at
        "demo user added manually for telegram demo"
    )
)

conn.commit()
conn.close()

print("✅ demo_user успешно добавлен в БД")
