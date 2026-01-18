import sys, os
import importlib
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import instagram_bot


def test_instagram_to_api_and_dm():
    # 🔄 СБРОС СОСТОЯНИЯ МОДУЛЯ
    importlib.reload(instagram_bot)

    username = "mock_user"
    fake_user_id = 111

    # --- Мокаем Instagram ---
    instagram_bot.cl = MagicMock()
    instagram_bot.get_user_id = MagicMock(return_value=fake_user_id)
    instagram_bot.is_subscribed = MagicMock(return_value=True)
    instagram_bot.send_dm = MagicMock()

    # --- Мокаем HTTP API ---
    with patch("instagram_bot.requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        instagram_bot.process_comment(username)

        urls = [call.args[0] for call in mock_post.call_args_list]

        assert any("/users" in url for url in urls), "API /users не вызван"
        assert any("/subscription" in url for url in urls), "API /subscription не вызван"

        assert instagram_bot.send_dm.call_count >= 1
        dm_text = instagram_bot.send_dm.call_args[0][1]

        assert "трейкер" in dm_text or "✅ Всё готово" in dm_text
        assert "t.me" in dm_text
