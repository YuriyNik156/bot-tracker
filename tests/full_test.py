import pytest
from unittest.mock import MagicMock, patch
import instagram_bot
from telegram_bot import cmd_start
import asyncio


@pytest.mark.asyncio
async def test_full_flow_logic():
    # --- Мокаем Instagram ---
    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=999)
    instagram_bot.is_subscribed = MagicMock(return_value=True)
    instagram_bot.send_dm = MagicMock()

    username = "user123"

    # Мокаем API
    with patch("instagram_bot.requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        # Вызов Instagram comment
        instagram_bot.process_comment(username)
        assert instagram_bot.send_dm.call_count == 2
        assert mock_post.call_count >= 1

    # --- Telegram часть ---
    class FakeMessage:
        def __init__(self):
            self.text = f"/start insta_{username}"
            self.from_user = type("User", (), {"id": 1, "username": "tg"})()

        async def answer(self, msg):
            self.last_msg = msg

    message = FakeMessage()

    with patch("telegram_bot.api_get_user") as mock_get_user, \
            patch("telegram_bot.api_mark_tracker_sent", new_callable=AsyncMock) as mock_tracker:
        mock_get_user.return_value = {"instagram_username": username, "tracker_sent_at": None}

        await cmd_start(message)

        mock_get_user.assert_called_once_with(username)
        mock_tracker.assert_awaited_once()
        assert "Готово" in message.last_msg
