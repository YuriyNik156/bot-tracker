from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime

import sqlite3
from database import init_db, DB_PATH

from logger import setup_logger


app = FastAPI(title="Tracker API")

logger = setup_logger("api_server")

def get_connection():
    return sqlite3.connect(DB_PATH)


@app.on_event("startup")
def startup():
    init_db()
    logger.info("API server started")


# ===== Pydantic-схемы =====

class UserCreate(BaseModel):
    instagram_username: str


class SubscriptionUpdate(BaseModel):
    instagram_username: str
    is_subscribed: bool


class TrackerSent(BaseModel):
    instagram_username: str
    telegram_user_id: int


# ===== Логирование входящих HTTP-запросов =====
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"REQUEST | {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        logger.info(
            f"RESPONSE | {request.method} {request.url.path} | status={response.status_code}"
        )
        return response

    except Exception as e:
        logger.error(
            f"UNHANDLED_EXCEPTION | {request.method} {request.url.path}",
            exc_info=True
        )
        raise

# ===== API эндпоинты =====

@app.post("/users")
def create_user(data: UserCreate):
    logger.info(f"CREATE_USER | instagram={data.instagram_username}")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE instagram_username = ?",
        (data.instagram_username,)
    )
    user = cursor.fetchone()

    if user:
        logger.info(f"USER_EXISTS | instagram={data.instagram_username}")
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

    logger.info(f"USER_CREATED | instagram={data.instagram_username}")
    return {"message": "User created"}


@app.post("/subscription")
def update_subscription(data: SubscriptionUpdate):
    logger.info(
        f"SUBSCRIPTION_UPDATE | instagram={data.instagram_username} | subscribed={data.is_subscribed}"
    )

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
        logger.warning(
            f"USER_NOT_FOUND | instagram={data.instagram_username}"
        )
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.commit()
    conn.close()

    logger.info(f"SUBSCRIPTION_OK | instagram={data.instagram_username}")
    return {"message": "Subscription status updated"}


@app.post("/tracker-sent")
def mark_tracker_sent(data: TrackerSent):
    logger.info(
        f"TRACKER_SENT | instagram={data.instagram_username} | telegram_id={data.telegram_user_id}"
    )

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
        logger.warning(
            f"TRACKER_FAIL | instagram={data.instagram_username}"
        )
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.commit()
    conn.close()

    logger.info(
        f"TRACKER_OK | instagram={data.instagram_username} | telegram_id={data.telegram_user_id}"
    )
    return {"message": "Tracker marked as sent"}
