from instagrapi import Client
import time
import os
from dotenv import load_dotenv

from logger import setup_logger

load_dotenv()

IG_USERNAME = os.getenv("INSTAGRAM_USERNAME")
IG_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
TARGET_ACCOUNT = os.getenv("INSTAGRAM_TARGET_ACCOUNT")
TG_BOT_LINK = os.getenv("TELEGRAM_BOT_LINK")

logger = setup_logger("instagram_bot")

cl = Client()


def login():
    cl.login(IG_USERNAME, IG_PASSWORD)
    logger.info("Instagram bot logged in")


def is_subscribed(user_id: int) -> bool:
    followers = cl.user_followers(cl.user_id_from_username(TARGET_ACCOUNT))
    return user_id in followers


def send_dm(user_id: int, text: str):
    cl.direct_send(text, [user_id])
    logger.info(f"DM sent | user_id={user_id}")


def process_comment(username: str):
    user_id = cl.user_id_from_username(username)

    logger.info(f"Trigger comment | instagram={username}")

    send_dm(
        user_id,
        "Готовлю трекер на отправку, давай проверим подписку 👇"
    )

    if is_subscribed(user_id):
        link = f"{TG_BOT_LINK}?start=insta_{username}"
        send_dm(user_id, f"Отлично! Вот твой Трекер 👉 {link}")
        logger.info(f"Subscribed | link sent | {username}")
    else:
        send_dm(
            user_id,
            "Подпишись на наш аккаунт и напиши сюда «Подписался»"
        )
        logger.warning(f"Not subscribed | {username}")


def main():
    login()

    logger.info("Instagram bot started")

    while True:
        # MVP: ручной список (потом заменишь на реальный listener)
        comments = cl.media_comments(media_id="REELS_ID")

        for comment in comments:
            if "трекер" in comment.text.lower():
                process_comment(comment.user.username)

        time.sleep(30)


if __name__ == "__main__":
    main()
