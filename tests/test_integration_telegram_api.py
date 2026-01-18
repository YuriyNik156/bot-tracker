import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch, AsyncMock
import pytest
from telegram_bot import cmd_start

class FakeMessage:
    def __init__(self, text, user_id=123, username="tg_user"):
        self.text = text
        self.from_user = type("User", (), {"id": user_id, "username": username})()
    async def answer(self, msg):
        self.last_answer = msg

@pytest.mark.asyncio
async def test_telegram_start_insta(tmp_path):
    message = FakeMessage("/start insta_testuser")

    # --- Мокаем API get_user ---
    with patch("telegram_bot.api_get_user") as mock_get_user, \
         patch("telegram_bot.api_mark_tracker_sent", new_callable=AsyncMock) as mock_tracker_sent:

        mock_get_user.return_value = {"instagram_username": "testuser", "tracker_sent_at": None}

        await cmd_start(message)

        # Проверяем, что API вызвался
        mock_get_user.assert_called_once_with("testuser")
        mock_tracker_sent.assert_awaited_once_with("testuser", 123)

        # Проверяем, что пользователь получил сообщение о выдаче
        assert "Готово" in message.last_answer
