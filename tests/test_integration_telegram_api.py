import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from telegram_bot import cmd_start

class FakeMessage:
    def __init__(self, text, user_id=123, username="tg_user"):
        self.text = text
        self.from_user = type("User", (), {"id": user_id, "username": username})()
        self.last_answer = None

    async def answer(self, msg):
        self.last_answer = msg

@pytest.mark.asyncio
async def test_telegram_start_insta_new_tracker():
    """Выдача трекера, если он ещё не был отправлен"""
    message = FakeMessage("/start insta_testuser")

    with patch("telegram_bot.api_get_user") as mock_get_user, \
         patch("telegram_bot.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_get_user.return_value = {"instagram_username": "testuser", "tracker_sent_at": None}

        # Мокаем ответ POST с status_code=200
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        await cmd_start(message)

        # Проверяем, что POST вызвался
        mock_post.assert_awaited_once()

        # Проверяем, что пользователю пришло сообщение о выдаче трекера
        assert "Готово" in message.last_answer or "трейкер" in message.last_answer

@pytest.mark.asyncio
async def test_telegram_start_insta_already_sent():
    """Поведение, если трекер уже был выдан"""
    message = FakeMessage("/start insta_testuser")

    with patch("telegram_bot.api_get_user") as mock_get_user, \
         patch("telegram_bot.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_get_user.return_value = {"instagram_username": "testuser", "tracker_sent_at": "2026-01-01T12:00:00"}

        await cmd_start(message)

        # POST не должен вызываться
        mock_post.assert_not_awaited()

        # Проверяем предупреждение пользователю
        assert "⚠️" in message.last_answer or "уже выдан" in message.last_answer
