from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import asyncio
import requests, os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.text)
async def handle_username(message: Message):
    instagram_username = message.text.strip()
    telegram_user_id = message.from_user.id

    try:
        response = requests.post(
            f"{API_BASE_URL}/tracker-sent",
            json={"instagram_username": instagram_username,
                  "telegram_user_id": telegram_user_id},
            timeout=5
        )
        if response.status_code == 200:
            await message.answer("Готово! Трекер отправлен ✅")
        else:
            await message.answer("Не нашёл пользователя 😕")
    except requests.RequestException:
        await message.answer("Сервер недоступен ⚠️")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
