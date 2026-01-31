"""
instagram_bot_instagrapi.py

Старая версия Instagram-бота на instagrapi.
Использует polling (опрос комментариев и DM).
Хранится для истории и сравнения с webhook-версией.
"""

import os
import time
import requests
from dotenv import load_dotenv

from instagrapi import Client
from instagrapi.exceptions import ClientConnectionError

from logger import setup_logger

# --------------------
# ENV
# --------------------
load_dotenv()

IG_USERNAME = os.getenv("INSTAGRAM_USERNAME")
IG_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

TG_BOT_LINK = os.getenv("TELEGRAM_BOT_LINK")
API_BASE_URL = os.getenv("API_BASE_URL")

POST_URL = "https://www.instagram.com/p/DTnRnyXjDVQ/"
SESSION_FILE = "ig_session.json"

if not all([IG_USERNAME, IG_PASSWORD, TG_BOT_LINK, API_BASE_URL]):
    raise RuntimeError("❌ Не все переменные окружения заданы")

# --------------------
# LOGGER
# --------------------
logger = setup_logger("instagram_bot_instagrapi")

# --------------------
# INSTAGRAM CLIENT
# --------------------
cl = Client()
cl.set_device({
    "app_version": "269.0.0.18.75",
    "android_version": 26,
    "android_release": "8.0.0",
    "dpi": "480dpi",
    "resolution": "1080x1920",
    "manufacturer": "Samsung",
    "device": "SM-G960F",
    "model": "Galaxy S9",
    "cpu": "qcom",
})

# --------------------
# LOGIN
# --------------------
def login():
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            logger.info("🟢 Instagram session loaded")
            return
        except Exception as e:
            logger.warning(f"⚠️ Session load failed: {e}")

    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.dump_settings(SESSION_FILE)
    logger.info("🟢 New Instagram login successful")

# --------------------
# API HELPERS
# --------------------
def api_create_user(instagram_username: str):
    try:
        requests.post(
            f"{API_BASE_URL}/users",
            json={"instagram_username": instagram_username},
            timeout=5,
        )
        logger.info(f"API user created or exists | {instagram_username}")
    except Exception as e:
        logger.error(f"API create_user error | {instagram_username} | {e}")

def api_mark_subscribed(instagram_username: str):
    try:
        requests.post(
            f"{API_BASE_URL}/subscription",
            json={
                "instagram_username": instagram_username,
                "is_subscribed": True,
            },
            timeout=5,
        )
        logger.info(f"API subscription marked | {instagram_username}")
    except Exception as e:
        logger.error(f"API subscription error | {instagram_username} | {e}")

# --------------------
# INSTAGRAM HELPERS
# --------------------
def get_user_id(username: str) -> int:
    return cl.user_info_by_username(username).pk

BOT_IG_USERNAME = IG_USERNAME
BOT_USER_ID = None

def is_subscribed(user_id: int) -> bool:
    global BOT_USER_ID

    try:
        if BOT_USER_ID is None:
            BOT_USER_ID = cl.user_id_from_username(BOT_IG_USERNAME)

        followers = cl.user_followers(user_id)
        subscribed = BOT_USER_ID in followers

        logger.info(
            f"Subscription check | user_id={user_id} | subscribed={subscribed}"
        )
        return subscribed

    except Exception as e:
        logger.warning(
            f"Subscription check failed | user_id={user_id} | {e}"
        )
        return False

def send_dm(user_id: int, text: str):
    cl.direct_send(text, [user_id])
    logger.info(f"DM sent | user_id={user_id} | text={text}")

# --------------------
# BUSINESS LOGIC
# --------------------
def process_comment(username: str):
    user_id = get_user_id(username)
    logger.info(f"💬 Trigger comment | instagram={username}")

    # 1. создаём пользователя
    api_create_user(username)

    # 2. проверяем подписку
    if is_subscribed(user_id):
        api_mark_subscribed(username)
        link = f"{TG_BOT_LINK}?start=insta_{username}"
        send_dm(
            user_id,
            f"✅ Всё готово! Вот твой трекер 👉 {link}"
        )
        logger.info(f"Subscribed immediately | link sent | {username}")
        return

    # 3. если не подписан — инструкция
    send_dm(
        user_id,
        "Подпишись на аккаунт и напиши сюда «Подписался» 🙌"
    )
    logger.info(f"Waiting for subscribe | {username}")

def process_dm(username: str, text: str):
    text = text.lower().strip()
    if text != "подписался":
        return

    user_id = get_user_id(username)

    if is_subscribed(user_id):
        api_mark_subscribed(username)
        link = f"{TG_BOT_LINK}?start=insta_{username}"
        send_dm(
            user_id,
            f"✅ Подписка подтверждена! Вот твой трекер 👉 {link}"
        )
        logger.info(f"Subscribed after confirm | {username}")
    else:
        send_dm(
            user_id,
            "Подписку пока не вижу 🙏 Попробуй ещё раз через минуту."
        )
        logger.info(f"Confirm failed | still not subscribed | {username}")

# --------------------
# MAIN LOOP (POLLING)
# --------------------
def main():
    login()

    media_id = cl.media_pk_from_url(POST_URL)
    logger.info(f"📡 Watching post | media_id={media_id}")

    processed_users = set()

    while True:
        try:
            comments = cl.media_comments(media_id)

        except ClientConnectionError as e:
            logger.warning(f"Instagram connection error: {e}")
            time.sleep(120)
            continue

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            time.sleep(300)
            continue

        for comment in comments:
            username = comment.user.username
            text = comment.text.lower()

            if "трекер" in text and username not in processed_users:
                process_comment(username)
                processed_users.add(username)

        time.sleep(120)

# --------------------
# ENTRY POINT
# --------------------
if __name__ == "__main__":
    main()
