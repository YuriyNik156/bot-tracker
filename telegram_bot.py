import telebot
import requests
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Напиши свой Instagram username, чтобы получить трекер 📊"
    )


@bot.message_handler(func=lambda message: True)
def handle_instagram_username(message):
    instagram_username = message.text.strip()
    telegram_user_id = message.from_user.id

    response = requests.post(
        f"{API_BASE_URL}/tracker-sent",
        json={
            "instagram_username": instagram_username,
            "telegram_user_id": telegram_user_id
        },
        timeout=5
    )

    if response.status_code == 200:
        bot.send_message(
            message.chat.id,
            "Готово! Трекер отправлен ✅"
        )
    else:
        bot.send_message(
            message.chat.id,
            "Не нашёл пользователя 😕 Проверь username или напиши позже."
        )


if __name__ == "__main__":
    print("Telegram bot is running...")
    bot.infinity_polling()
