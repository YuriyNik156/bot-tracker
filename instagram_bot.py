from instagrapi import Client
import time
import os
from dotenv import load_dotenv

from instagrapi.exceptions import ClientConnectionError

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
        try:
            cl.load_settings(SESSION_FILE)
            logger.info("Instagram session loaded")
            return
        except Exception as e:
            logger.warning(f"Failed to load session, relogin required: {e}")

    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.dump_settings(SESSION_FILE)
    logger.info("New Instagram login successful")


# --------------------
# HELPERS
# --------------------
def get_user_id(username: str) -> int:
    user = cl.user_info_by_username(username)
    return user.pk


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

def process_dm(username: str, text: str):
    user_id = get_user_id(username)
    text = text.lower().strip()

    if text == "подписался":
        if is_subscribed(user_id):
            link = f"{TG_BOT_LINK}?start=insta_{username}"
            send_dm(user_id, f"Отлично! Вот твой Трекер 👉 {link}")
            logger.info(f"Subscribed after confirm | instagram={username}")
        else:
            send_dm(
                user_id,
                "Подписку пока не вижу 🙏 Попробуй ещё раз через минуту."
            )
            logger.warning(
                f"Confirm failed | still not subscribed | instagram={username}"
            )


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
        logger.info(f"Waiting for subscribe | instagram={username}")

    def can_issue_tracker(instagram_username: str) -> bool:
        # вернуть False, если tracker_issued_at уже есть
        return True

    if not can_issue_tracker(username):
        send_dm(
            user_id,
            "Трекер уже был выдан 🙂 Если потерял — напиши в поддержку."
        )
        return


# --------------------
# MAIN LOOP
# --------------------
def main():
    login()

    media_id = cl.media_pk_from_url(POST_URL)
    logger.info(f"Watching post | media_id={media_id}")

    processed_users = set()

    while True:
        try:
            comments = cl.media_comments(media_id)
        except ClientConnectionError as e:
            logger.warning(f"Instagram connection error: {e}")
            logger.info("Sleeping 2 minutes before retry...")
            time.sleep(120)
            continue
        except Exception as e:
            logger.exception(f"Unexpected error while fetching comments: {e}")
            time.sleep(300)
            continue

        for comment in comments:
            text = comment.text.lower()
            username = comment.user.username

            if "трекер" in text and username not in processed_users:
                process_comment(username)
                processed_users.add(username)

        time.sleep(120)


# --------------------
# ENTRY POINT
# --------------------
if __name__ == "__main__":
    main()
