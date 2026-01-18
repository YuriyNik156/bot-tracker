import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch
import instagram_bot

def test_instagram_to_api_and_dm():
    fake_user_id = 111
    username = "mock_user"

    # --- Мокаем Instagram client ---
    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=fake_user_id)
    instagram_bot.is_subscribed = MagicMock(return_value=True)
    instagram_bot.send_dm = MagicMock()

    # --- Мокаем requests.post для API ---
    with patch("instagram_bot.requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        instagram_bot.process_comment(username)

        # Проверяем, что API /users вызвался
        mock_post.assert_any_call(
            f"{instagram_bot.API_BASE_URL}/users",
            json={"instagram_username": username},
            timeout=5
        )

        # Проверяем, что /subscription вызвался
        mock_post.assert_any_call(
            f"{instagram_bot.API_BASE_URL}/subscription",
            json={"instagram_username": username},
            timeout=5
        )

        # Проверяем отправку DM
        assert instagram_bot.send_dm.call_count == 2
