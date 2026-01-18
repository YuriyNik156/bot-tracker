import sys, os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import instagram_bot
from telegram_bot import cmd_start


@pytest.mark.asyncio
async def test_full_flow_logic():
    username = "user123"

    # -----------------------------
    # --- Мокаем Instagram ---
    # -----------------------------
    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=999)
    instagram_bot.is_subscribed = MagicMock(return_value=True)
    instagram_bot.send_dm = MagicMock()

    with patch("instagram_bot.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        if hasattr(instagram_bot, "process_comment"):
            instagram_bot.process_comment(username)

        assert instagram_bot.send_dm.call_count >= 1
        assert mock_post.call_count >= 1

    # -----------------------------
    # --- Мокаем Telegram ---
    # -----------------------------
    class FakeMessage:
        def __init__(self):
            self.text = f"/start insta_{username}"
            self.from_user = type("User", (), {"id": 123, "username": "tg_user"})()
            self.last_msg = None

        async def answer(self, msg):
            self.last_msg = msg

    message = FakeMessage()

    # Создаем мок, который возвращает объект с .status_code = 200
    class MockResponse:
        status_code = 200

    with patch("telegram_bot.api_get_user") as mock_get_user, \
         patch("telegram_bot.api_mark_tracker_sent", new_callable=AsyncMock) as mock_tracker:

        mock_get_user.return_value = {"instagram_username": username, "tracker_sent_at": None}
        mock_tracker.return_value = MockResponse()  # ✅ имитируем успешный POST

        await cmd_start(message)

        # Проверяем вызовы API
        mock_get_user.assert_called_once_with(username)
        mock_tracker.assert_awaited_once_with(username, 123)

        # Теперь бот должен ответить "Готово"
        assert "Готово" in message.last_msg or "трейкер" in message.last_msg
