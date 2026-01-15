from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import asyncio
import requests, os
from dotenv import load_dotenv
import httpx

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.commands("start"))
async def cmd_start(message: Message):
    args = message.get_args()
    if args:
        instagram_username = args
        telegram_user_id = message.from_user.id
        # отправляем сразу на API
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
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{API_BASE_URL}/tracker-sent",
                json={
                    "instagram_username": instagram_username,
                    "telegram_user_id": telegram_user_id
                }
            )

        if response.status_code == 200:
            await message.answer("Готово! Трекер отправлен ✅")
        else:
            await message.answer("Не нашёл пользователя 😕")

    except httpx.RequestError:
        await message.answer("Сервер недоступен ⚠️")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
