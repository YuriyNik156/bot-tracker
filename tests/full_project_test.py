import sys, os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# --- добавляем путь к проекту ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import instagram_bot
from telegram_bot import cmd_start


@pytest.mark.asyncio
async def test_full_mvp_flow():
    """
    Проверка полного MVP-потока:
    1. Комментарий в Instagram
    2. Вызов API /users и /subscription
    3. Отправка DM с трекером
    4. Telegram бот обрабатывает /start insta_
    5. Проверка защиты от повторной выдачи
    """

    username = "test_user"
    fake_user_id = 123
    telegram_user_id = 999

    # -----------------------------
    # --- Мокаем Instagram ---
    # -----------------------------
    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=fake_user_id)
    instagram_bot.is_subscribed = MagicMock(return_value=True)
    instagram_bot.send_dm = MagicMock()

    with patch("instagram_bot.requests.post") as mock_requests_post:
        mock_requests_post.return_value.status_code = 200

        # --- Шаг 1: комментарий в Instagram ---
        if hasattr(instagram_bot, "process_comment"):
            instagram_bot.process_comment(username)

        # Проверяем вызов API /users и /subscription
        assert mock_requests_post.call_count >= 2
        urls = [call.args[0] for call in mock_requests_post.call_args_list]
        assert any("/users" in url for url in urls)
        assert any("/subscription" in url for url in urls)

        # Проверяем отправку DM через Instagram
        assert instagram_bot.send_dm.call_count >= 1

    # -----------------------------
    # --- Мокаем Telegram ---
    # -----------------------------
    class FakeMessage:
        def __init__(self):
            self.text = f"/start insta_{username}"
            self.from_user = type("User", (), {"id": telegram_user_id, "username": "tg_user"})()
            self.last_msg = None

        async def answer(self, msg):
            self.last_msg = msg

    # Мокаем API бота и возвращаем объект с .status_code = 200
    class MockResponse:
        status_code = 200

    with patch("telegram_bot.api_get_user") as mock_api_get_user, \
         patch("telegram_bot.api_mark_tracker_sent", new_callable=AsyncMock) as mock_api_mark_sent:

        # -----------------------------
        # Первый вызов Telegram (трекер не был отправлен)
        # -----------------------------
        mock_api_get_user.return_value = {"instagram_username": username, "tracker_sent_at": None}
        mock_api_mark_sent.return_value = MockResponse()

        message = FakeMessage()
        await cmd_start(message)

        mock_api_get_user.assert_called_once_with(username)
        mock_api_mark_sent.assert_awaited_once_with(username, telegram_user_id)
        assert message.last_msg is not None
        assert "Готово" in message.last_msg or "трейкер" in message.last_msg

        # -----------------------------
        # Второй вызов Telegram (трекер уже был отправлен)
        # -----------------------------
        mock_api_get_user.reset_mock()
        mock_api_mark_sent.reset_mock()
        mock_api_get_user.return_value = {"instagram_username": username, "tracker_sent_at": "2026-01-18T12:00:00"}

        message_repeat = FakeMessage()
        await cmd_start(message_repeat)

        mock_api_get_user.assert_called_once_with(username)
        mock_api_mark_sent.assert_not_awaited()
        assert "уже был выдан" in message_repeat.last_msg or "⚠️" in message_repeat.last_msg
