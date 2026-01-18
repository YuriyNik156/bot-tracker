# tests/test_full_project.py
import sys, os
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# --- добавляем путь к проекту ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import instagram_bot
import telegram_bot


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

    # --- Мокаем Instagram client ---
    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=fake_user_id)
    instagram_bot.is_subscribed = MagicMock(return_value=True)
    instagram_bot.send_dm = MagicMock()

    # --- Мокаем API ---
    with patch("instagram_bot.requests.post") as mock_requests_post, \
         patch("telegram_bot.requests.post") as mock_telegram_post, \
         patch("telegram_bot.api_get_user") as mock_api_get_user, \
         patch("telegram_bot.api_mark_tracker_sent", new_callable=AsyncMock) as mock_api_mark_sent:

        # Настройки мока
        mock_requests_post.return_value.status_code = 200
        mock_telegram_post.return_value.status_code = 200
        mock_api_get_user.return_value = {"instagram_username": username, "tracker_sent_at": None}

        # --- Шаг 1: комментарий в Instagram ---
        instagram_bot.process_comment(username)

        # Проверяем вызов API /users и /subscription
        assert mock_requests_post.call_count >= 2
        urls = [call.args[0] for call in mock_requests_post.call_args_list]
        assert any("/users" in url for url in urls)
        assert any("/subscription" in url for url in urls)

        # Проверяем отправку DM через Instagram
        assert instagram_bot.send_dm.call_count == 2
        dm_texts = [call.args[1] if len(call.args) > 1 else call.args[0] for call in instagram_bot.send_dm.call_args_list]
        assert any("Готовлю трекер" in t for t in dm_texts)
        assert any("t.me" in t for t in dm_texts)

        # --- Шаг 2: Telegram /start insta_ ---
        class FakeMessage:
            def __init__(self):
                self.text = f"/start insta_{username}"
                self.from_user = type("User", (), {"id": telegram_user_id, "username": "tg_user"})()
                self.last_msg = None

            async def answer(self, msg):
                self.last_msg = msg

        message = FakeMessage()
        await telegram_bot.cmd_start(message)

        # Проверяем, что Telegram бот вызвал API get_user
        mock_api_get_user.assert_called_once_with(username)

        # Проверяем, что Telegram бот отметил tracker sent
        mock_api_mark_sent.assert_awaited_once_with(username, telegram_user_id)

        # Проверяем сообщение пользователю
        assert message.last_msg is not None
        assert "Готово" in message.last_msg

        # --- Шаг 3: повторная выдача трекера ---
        # Если tracker_sent_at уже есть
        mock_api_get_user.return_value = {"instagram_username": username, "tracker_sent_at": "2026-01-18T12:00:00"}

        message_repeat = FakeMessage()
        await telegram_bot.cmd_start(message_repeat)

        assert "уже был выдан" in message_repeat.last_msg
