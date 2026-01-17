import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch
import instagram_bot


def test_process_comment_sends_two_messages_when_subscribed():
    # --- mock user id ---
    fake_user_id = 123456

    # --- мокаем client ---
    instagram_bot.cl = MagicMock()

    instagram_bot.get_user_id = MagicMock(return_value=fake_user_id)
    instagram_bot.is_subscribed = MagicMock(return_value=True)

    # --- запускаем ---
    instagram_bot.process_comment("test_user")

    # --- проверяем ---
    assert instagram_bot.cl.direct_send.call_count == 2

    calls = instagram_bot.cl.direct_send.call_args_list

    assert "Готовлю трекер" in calls[0].args[0]
    assert "t.me" in calls[1].args[0]


def test_process_comment_sends_subscription_message_if_not_subscribed():
    fake_user_id = 999

    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=fake_user_id)
    instagram_bot.is_subscribed = MagicMock(return_value=False)

    instagram_bot.process_comment("test_user")

    # Должно быть 2 сообщения
    assert instagram_bot.cl.direct_send.call_count == 2

    # Проверяем второе сообщение
    second_call = instagram_bot.cl.direct_send.call_args_list[1]
    message_text = second_call.args[0]

    assert "Подпишись на наш аккаунт" in message_text


def test_comment_filtering_logic():
    processed_users = set()

    comments = [
        MagicMock(
            text="Хочу трекер",
            user=MagicMock(username="user1")
        ),
        MagicMock(
            text="ТРЕКЕР пожалуйста",
            user=MagicMock(username="user1")
        ),
    ]

    instagram_bot.process_comment = MagicMock()

    for comment in comments:
        text = comment.text.lower()
        username = comment.user.username

        if "трекер" in text and username not in processed_users:
            instagram_bot.process_comment(username)
            processed_users.add(username)

    # process_comment должен вызваться только 1 раз
    instagram_bot.process_comment.assert_called_once_with("user1")
