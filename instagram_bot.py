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

if not all([VERIFY_TOKEN, TG_BOT_LINK, API_BASE_URL, IG_PAGE_ACCESS_TOKEN]):
    raise RuntimeError("❌ Не все переменные окружения заданы")

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
        timeout=5,
    )


def api_mark_subscribed(instagram_username: str):
    requests.post(
        f"{API_BASE_URL}/subscription",
        json={
            "instagram_username": instagram_username,
            "is_subscribed": True,
        },
        timeout=5,
    )


# --------------------
# INSTAGRAM GRAPH API
# --------------------
def send_dm(instagram_user_id: str, text: str):
    url = f"{GRAPH_API_URL}/me/messages"
    payload = {
        "recipient": {"id": instagram_user_id},
        "message": {"text": text},
    }
    params = {"access_token": IG_PAGE_ACCESS_TOKEN}

    r = requests.post(url, params=params, json=payload, timeout=5)
    r.raise_for_status()

    logger.info(f"📩 DM sent | ig_user_id={instagram_user_id}")


# --------------------
# BUSINESS LOGIC
# --------------------
def handle_tracker_request(instagram_user_id: str, username: str):
    api_create_user(username)

    link = f"{TG_BOT_LINK}?start=insta_{username}"
    send_dm(
        instagram_user_id,
        f"✅ Всё готово!\nВот твой трекер 👉 {link}",
    )

    logger.info(f"🔗 Tracker sent | {username}")


# --------------------
# WEBHOOK VERIFY (GET)
# --------------------
@app.get("/webhook/instagram")
def verify_webhook(
    hub_mode: str | None = None,
    hub_challenge: str | None = None,
    hub_verify_token: str | None = None,
):
    logger.info("🔎 Webhook verification request received")

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return int(hub_challenge)

    logger.warning("❌ Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


# --------------------
# WEBHOOK RECEIVER (POST)
# --------------------
@app.post("/webhook/instagram")
async def webhook_receiver(request: Request):
    data = await request.json()
    logger.debug(f"Incoming webhook: {data}")

    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):

            sender_id = messaging.get("sender", {}).get("id")
            message = messaging.get("message", {})
            text = message.get("text", "")

            if not sender_id or not text:
                continue

            logger.info(f"💬 Message from {sender_id}: {text}")

            if "трекер" in text.lower():
                username = f"ig_{sender_id}"
                handle_tracker_request(sender_id, username)

    return {"status": "ok"}


# --------------------
# ROOT (healthcheck)
# --------------------
@app.get("/")
def root():
    return {"status": "instagram webhook server is running"}
