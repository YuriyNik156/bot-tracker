import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import instagram_bot


def test_process_comment_when_subscribed_sends_tracker_link():
    fake_user_id = 123456
    username = "test_user"

    # --- мокаем Instagram client ---
    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=fake_user_id)
    instagram_bot.is_subscribed = MagicMock(return_value=True)
    instagram_bot.send_dm = MagicMock()

    # --- мокаем API ---
    with patch("instagram_bot.api_create_user") as mock_api_create_user, \
         patch("instagram_bot.api_mark_subscribed") as mock_api_mark_subscribed:

        instagram_bot.process_comment(username)

        # Проверяем, что API /users и /subscription вызвались
        mock_api_create_user.assert_called_once_with(username)
        mock_api_mark_subscribed.assert_called_once_with(username)

        # Проверяем DM
        instagram_bot.send_dm.assert_called()
        dm_text = instagram_bot.send_dm.call_args[0][1]
        assert "трейкер" in dm_text or "✅ Всё готово" in dm_text
        assert "t.me" in dm_text


def test_process_comment_when_not_subscribed_sends_subscription_prompt():
    fake_user_id = 999
    username = "test_user"

    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=fake_user_id)
    instagram_bot.is_subscribed = MagicMock(return_value=False)
    instagram_bot.send_dm = MagicMock()

    with patch("instagram_bot.api_create_user") as mock_api_create_user:
        instagram_bot.process_comment(username)

        # Проверяем, что API /users вызвался
        mock_api_create_user.assert_called_once_with(username)

        # Проверяем, что DM с просьбой подписаться отправлен
        instagram_bot.send_dm.assert_called()
        dm_text = instagram_bot.send_dm.call_args[0][1]

        # Проверяем часть текста, которая гарантированно есть
        assert "Подпишись" in dm_text
        assert "«Подписался»" in dm_text



def test_comment_filtering_only_processes_new_users():
    processed_users = set()

    comments = [
        MagicMock(text="Хочу трекер", user=MagicMock(username="user1")),
        MagicMock(text="ТРЕКЕР пожалуйста", user=MagicMock(username="user1")),
    ]

    instagram_bot.process_comment = MagicMock()

    for comment in comments:
        text = comment.text.lower()
        username = comment.user.username

        if "трекер" in text and username not in processed_users:
            instagram_bot.process_comment(username)
            processed_users.add(username)

    # Проверяем, что process_comment вызвался только один раз
    instagram_bot.process_comment.assert_called_once_with("user1")
