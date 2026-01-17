# from instagrapi import Client
import time
import os
from dotenv import load_dotenv

from logger import setup_logger

load_dotenv()

# IG_USERNAME = os.getenv("INSTAGRAM_USERNAME")
# IG_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
# TARGET_ACCOUNT = os.getenv("INSTAGRAM_TARGET_ACCOUNT")
TG_BOT_LINK = os.getenv("TELEGRAM_BOT_LINK")

logger = setup_logger("instagram_bot")

# cl = Client()


# def login():
#     cl.login(IG_USERNAME, IG_PASSWORD)
#     logger.info("Instagram bot logged in")

def get_user_id(username: str) -> int:
    return abs(hash(username)) % 10_000_000

def is_subscribed(user_id: int) -> bool:
    return True  # mock

def send_dm(user_id: int, text: str):
    logger.info(f"MOCK DM | user_id={user_id} | text={text}")



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
    logger.info("=== LOCAL TEST START ===")

    test_users = [
        "test_user",
        "ghost",
        "real_instagram_name"
    ]

    for username in test_users:
        process_comment(username)

    logger.info("=== LOCAL TEST END ===")
