import os
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from logger import setup_logger

# --------------------
# ENV
# --------------------
load_dotenv()

VERIFY_TOKEN = os.getenv("IG_VERIFY_TOKEN", "dev_verify_token")
TG_BOT_LINK = os.getenv("TELEGRAM_BOT_LINK")
API_BASE_URL = os.getenv("API_BASE_URL")
IG_PAGE_ACCESS_TOKEN = os.getenv("IG_PAGE_ACCESS_TOKEN")  # может быть None

GRAPH_API_URL = "https://graph.facebook.com/v18.0"

if not all([TG_BOT_LINK, API_BASE_URL]):
    raise RuntimeError("❌ TG_BOT_LINK или API_BASE_URL не заданы")

INSTAGRAM_ENABLED = IG_PAGE_ACCESS_TOKEN is not None

# --------------------
# LOGGER
# --------------------
logger = setup_logger("instagram_webhook")

if INSTAGRAM_ENABLED:
    logger.info("🟢 Instagram Graph API ENABLED")
else:
    logger.warning("🟡 Instagram Graph API DISABLED (dev mode)")

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
    if not INSTAGRAM_ENABLED:
        logger.info(
            f"🧪 [MOCK] DM to {instagram_user_id}: {text}"
        )
        return

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

    logger.info(f"🔗 Tracker processed | {username}")


# --------------------
# WEBHOOK VERIFY (GET)
# --------------------
@app.get("/webhook/instagram")
def verify_webhook(request: Request):
    logger.info("🔎 Webhook verification request received")

    params = request.query_params

    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    verify_token = params.get("hub.verify_token")

    if mode == "subscribe" and verify_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return PlainTextResponse(content=challenge, status_code=200)

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
    return {
        "status": "instagram webhook server is running",
        "instagram_enabled": INSTAGRAM_ENABLED,
    }
