from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

import asyncio
import os
import requests
from dotenv import load_dotenv
from httpx import AsyncClient, RequestError, TimeoutException

from logger import setup_logger


# --------------------
# ENV
# --------------------
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")


# --------------------
# BOT SETUP
# --------------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logger = setup_logger("telegram_bot")


# --------------------
# API HELPERS
# --------------------
def api_get_user(instagram_username: str):
    try:
        response = requests.get(
            f"{API_BASE_URL}/users/{instagram_username}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"API get_user error | {instagram_username} | {e}")
    return None
    print("DEBUG: requesting user", instagram_username)


async def api_mark_tracker_sent(instagram_username: str, telegram_user_id: int):
    async with AsyncClient(timeout=5) as client:
        return await client.post(
            f"{API_BASE_URL}/tracker-sent",
            json={
                "instagram_username": instagram_username,
                "telegram_user_id": telegram_user_id
            }
        )


# --------------------
# COMMAND /start
# --------------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(
        f"/start | telegram_id={message.from_user.id} | username={message.from_user.username}"
    )

    parts = (message.text or "").split(maxsplit=1)

    # --- кейс: пришли из Instagram ---
    if len(parts) == 2 and parts[1].startswith("insta_"):
        instagram_username = parts[1].replace("insta_", "")
        telegram_user_id = message.from_user.id

        user_data = api_get_user(instagram_username)

        if not user_data:
            await message.answer(
                "❌ Я не нашёл тебя в базе.\n"
                "Напиши слово «трекер» под рилсом в Instagram 👇"
            )
            return

        if user_data.get("tracker_sent_at"):
            await message.answer(
                "⚠️ Трекер уже был выдан ранее.\n"
                "Если потерял — напиши в поддержку 🙂"
            )
            return

        try:
            response = await api_mark_tracker_sent(
                instagram_username,
                telegram_user_id
            )

            if response.status_code == 200:
                await message.answer("✅ Готово! Трекер отправлен 🎉")
            elif response.status_code == 404:
                await message.answer("❌ Пользователь не найден")
            else:
                await message.answer("⚠️ Что-то пошло не так, попробуй позже")

        except TimeoutException:
            await message.answer("⏳ Сервер долго отвечает, попробуй позже")
        except RequestError:
            await message.answer("⚠️ Сервер временно недоступен")

        return

    # --- обычный старт ---
    await message.answer(
        "Привет! 👋\n"
        "Чтобы получить трекер:\n"
        "1️⃣ Напиши «трекер» под рилсом в Instagram\n"
        "2️⃣ Перейди по ссылке из Direct\n"
    )


# --------------------
# FALLBACK (на случай текста)
# --------------------
@dp.message(F.text & ~F.text.regexp(r'^\s*$'))
async def fallback(message: Message):
    await message.answer(
        "Чтобы получить трекер, перейди по ссылке из Instagram 🙌"
    )


# --------------------
# ENTRY POINT
# --------------------
async def main():
    logger.info("Telegram bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
