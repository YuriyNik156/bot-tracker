from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime

import sqlite3
from database import init_db, DB_PATH

from logger import setup_logger


app = FastAPI(title="Tracker API")

logger = setup_logger("api_server")

def get_connection():
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        logger.error(f"DB connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


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
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE instagram_username = ?",
            (data.instagram_username,)
        )
        if cursor.fetchone():
            logger.info(f"User already exists: {data.instagram_username}")
            return {"message": "User already exists"}

        cursor.execute(
            "INSERT INTO users (instagram_username, logs) VALUES (?, ?)",
            (data.instagram_username, "user_created")
        )

        conn.commit()
        logger.info(f"User created: {data.instagram_username}")
        return {"message": "User created"}

    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        conn.close()



@app.post("/subscription")
def update_subscription(data: SubscriptionUpdate):
    try:
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
            logger.info(f"Subscription update failed: {data.instagram_username}")
            raise HTTPException(status_code=404, detail="User not found")

        conn.commit()
        logger.info(f"Subscription updated: {data.instagram_username}")
        return {"message": "Subscription updated"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Subscription error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        conn.close()


@app.post("/tracker-sent")
def mark_tracker_sent(data: TrackerSent):
    try:
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
            logger.info(f"Tracker send failed: {data.instagram_username}")
            raise HTTPException(status_code=404, detail="User not found")

        conn.commit()
        logger.info(f"Tracker sent: {data.instagram_username}")
        return {"message": "Tracker marked as sent"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Tracker error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        conn.close()


@app.get("/users/{instagram_username}")
def get_user(instagram_username: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT instagram_username, telegram_user_id, tracker_sent_at
            FROM users
            WHERE instagram_username = ?
            """,
            (instagram_username,)
        )

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "instagram_username": row[0],
            "telegram_user_id": row[1],
            "tracker_sent_at": row[2],
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        conn.close()
