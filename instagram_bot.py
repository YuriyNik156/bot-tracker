from instagrapi import Client
import time
import os
from dotenv import load_dotenv

from logger import setup_logger

# --------------------
# ENV
# --------------------
load_dotenv()

IG_USERNAME = os.getenv("INSTAGRAM_USERNAME")
IG_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
TG_BOT_LINK = os.getenv("TELEGRAM_BOT_LINK")

POST_URL = "https://www.instagram.com/p/DTnRnyXjDVQ/"
SESSION_FILE = "ig_session.json"

# --------------------
# LOGGER
# --------------------
logger = setup_logger("instagram_bot")

# --------------------
# INSTAGRAM CLIENT
# --------------------
cl = Client()

# Device fingerprint (маскируемся под Android)
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
# LOGIN WITH SESSION
# --------------------
def login():
    if os.path.exists(SESSION_FILE):
        cl.load_settings(SESSION_FILE)
        logger.info("Instagram session loaded")

    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.dump_settings(SESSION_FILE)

    logger.info("Instagram bot logged in successfully")


# --------------------
# HELPERS
# --------------------
def get_user_id(username: str) -> int:
    user = cl.user_info_by_username(username)
    return user.pk


def is_subscribed(user_id: int) -> bool:
    # пока mock — позже подключишь реальную проверку
    return True


def send_dm(user_id: int, text: str):
    cl.direct_send(text, [user_id])
    logger.info(f"Sent DM | user_id={user_id} | text={text}")


def process_comment(username: str):
    user_id = get_user_id(username)

    logger.info(f"Trigger comment | instagram={username} | user_id={user_id}")

    send_dm(
        user_id,
        "Готовлю трекер на отправку, давай проверим подписку 👇"
    )

    if is_subscribed(user_id):
        link = f"{TG_BOT_LINK}?start=insta_{username}"
        send_dm(user_id, f"Отлично! Вот твой Трекер 👉 {link}")
        logger.info(f"Subscribed | link sent | instagram={username}")
    else:
        send_dm(
            user_id,
            "Подпишись на наш аккаунт и напиши сюда «Подписался»"
        )
        logger.warning(f"Not subscribed | instagram={username}")


# --------------------
# MAIN LOOP
# --------------------
def main():
    login()

    media_id = cl.media_pk_from_url(POST_URL)
    logger.info(f"Watching post | media_id={media_id}")

    processed_users = set()  # защита от спама

    while True:
        comments = cl.media_comments(media_id)

        for comment in comments:
            text = comment.text.lower()
            username = comment.user.username

            if "трекер" in text and username not in processed_users:
                process_comment(username)
                processed_users.add(username)

        time.sleep(30)


# --------------------
# ENTRY POINT
# --------------------
if __name__ == "__main__":
    main()
