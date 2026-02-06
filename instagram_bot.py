# instagram_bot.py
import os
import requests
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

from logger import setup_logger

# --------------------
# ENV
# --------------------
load_dotenv()

VERIFY_TOKEN = os.getenv("IG_VERIFY_TOKEN")
TG_BOT_LINK = os.getenv("TELEGRAM_BOT_LINK")
API_BASE_URL = os.getenv("API_BASE_URL")
IG_PAGE_ACCESS_TOKEN = os.getenv("IG_PAGE_ACCESS_TOKEN")

GRAPH_API_URL = "https://graph.facebook.com/v18.0"

# --------------------
# LOGGER
# --------------------
logger = setup_logger("instagram_webhook")

# --------------------
# FASTAPI
# --------------------
app = FastAPI()


# --------------------
# API HELPERS
# --------------------
def api_create_user(instagram_username: str):
    requests.post(
        f"{API_BASE_URL}/users",
        json={"instagram_username": instagram_username},
        timeout=5
    )


def api_mark_subscribed(instagram_username: str):
    requests.post(
        f"{API_BASE_URL}/subscription",
        json={
            "instagram_username": instagram_username,
            "is_subscribed": True
        },
        timeout=5
    )


# --------------------
# INSTAGRAM GRAPH HELPERS
# --------------------
def send_dm(instagram_user_id: str, text: str):
    url = f"{GRAPH_API_URL}/me/messages"
    payload = {
        "recipient": {"id": instagram_user_id},
        "message": {"text": text}
    }
    params = {"access_token": IG_PAGE_ACCESS_TOKEN}

    r = requests.post(url, params=params, json=payload, timeout=5)
    r.raise_for_status()

    logger.info(f"DM sent | ig_user_id={instagram_user_id}")


# --------------------
# BUSINESS LOGIC
# --------------------
def handle_tracker_request(instagram_user_id: str, username: str):
    api_create_user(username)

    link = f"{TG_BOT_LINK}?start=insta_{username}"
    send_dm(
        instagram_user_id,
        f"✅ Всё готово! Вот твой трекер 👉 {link}"
    )

    logger.info(f"Tracker sent | {username}")


# --------------------
# WEBHOOK VERIFY
# --------------------
@app.get("/webhook/instagram")
def verify(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    if hub_verify_token != VERIFY_TOKEN:
        raise HTTPException(status_code=403)

    return int(hub_challenge)


# --------------------
# WEBHOOK RECEIVER
# --------------------
@app.post("/webhook/instagram")
async def webhook(request: Request):
    data = await request.json()
    logger.debug(data)

    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):

            sender_id = messaging["sender"]["id"]
            message = messaging.get("message", {})
            text = message.get("text", "").lower()

            if "трекер" in text:
                username = f"ig_{sender_id}"  # fallback
                handle_tracker_request(sender_id, username)

    return {"status": "ok"}
