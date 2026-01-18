from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
import requests, os
from dotenv import load_dotenv
from httpx import AsyncClient, RequestError, TimeoutException

from logger import setup_logger


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logger = setup_logger("telegram_bot")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = message.text or ""
    parts = text.split(maxsplit=1)
    args = message.text.split(maxsplit=1)

    logger.info(
        f"/start | telegram_id={message.from_user.id} | username={message.from_user.username}"
    )

    if len(parts) > 1 and args[1].startswith("insta_"):
        args = parts[1]
        instagram_username = parts[1].replace("insta_", "")
        telegram_user_id = message.from_user.id

        await send_to_api(instagram_username, telegram_user_id, message)
    else:
        await message.answer(
            "Привет! 👋\n"
            "Напиши свой Instagram username, чтобы получить трекер 📊"
        )


@dp.message(F.text & ~F.text.regexp(r'^\s*$'))
async def handle_username(message: Message):
    instagram_username = message.text.strip()
    telegram_user_id = message.from_user.id

    try:
        async with AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{API_BASE_URL}/tracker-sent",
                json={
                    "instagram_username": instagram_username,
                    "telegram_user_id": telegram_user_id
                }
            )

        if response.status_code == 200:
            await message.answer("Готово! Трекер отправлен ✅")
        elif response.status_code == 404:
            await message.answer("Пользователь не найден 😕")
        else:
            await message.answer("Что-то пошло не так ⚠️")

    except TimeoutException:
        await message.answer("Сервер долго отвечает ⏳ Попробуй позже")

    except RequestError:
        await message.answer("Сервер временно недоступен ⚠️")

async def main():
    logger.info("Telegram bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
