from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

import sqlite3
from database import init_db, DB_PATH


app = FastAPI(title="Tracker API")


def get_connection():
    return sqlite3.connect(DB_PATH)


@app.on_event("startup")
def startup():
    init_db()


# ===== Pydantic-схемы =====

class UserCreate(BaseModel):
    instagram_username: str


class SubscriptionUpdate(BaseModel):
    instagram_username: str
    is_subscribed: bool


class TrackerSent(BaseModel):
    instagram_username: str
    telegram_user_id: int


# ===== API эндпоинты =====

@app.post("/users")
def create_user(data: UserCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE instagram_username = ?",
        (data.instagram_username,)
    )
    user = cursor.fetchone()

    if user:
        conn.close()
        return {"message": "User already exists"}

    cursor.execute(
        """
        INSERT INTO users (instagram_username, logs)
        VALUES (?, ?)
        """,
        (data.instagram_username, "user_created")
    )

    conn.commit()
    conn.close()

    return {"message": "User created"}


@app.post("/subscription")
def update_subscription(data: SubscriptionUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET is_subscribed = ?, logs = ?
        WHERE instagram_username = ?
        """,
        (int(data.is_subscribed), "subscription_updated", data.instagram_username)
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.commit()
    conn.close()

    return {"message": "Subscription status updated"}


@app.post("/tracker-sent")
def mark_tracker_sent(data: TrackerSent):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET telegram_user_id = ?, tracker_sent_at = ?, logs = ?
        WHERE instagram_username = ?
        """,
        (
            data.telegram_user_id,
            datetime.utcnow().isoformat(),
            "tracker_sent",
            data.instagram_username
        )
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.commit()
    conn.close()

    return {"message": "Tracker marked as sent"}
