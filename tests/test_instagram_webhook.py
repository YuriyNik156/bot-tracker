import os
from fastapi.testclient import TestClient
from unittest.mock import patch

# важно: env ДО импорта приложения
os.environ["IG_VERIFY_TOKEN"] = "test_verify_token"
os.environ["TG_BOT_LINK"] = "https://t.me/test_bot"
os.environ["API_BASE_URL"] = "http://api.test"

from instagram_bot_graphs_api import app

client = TestClient(app)

# --------------------
# WEBHOOK VERIFY (GET)
# --------------------

def test_webhook_verify_success():
    response = client.get(
        "/webhook/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "12345",
        },
    )

    assert response.status_code == 200
    assert response.text == "12345"


def test_webhook_verify_fail():
    response = client.get(
        "/webhook/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "12345",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Verification failed"

# --------------------
# WEBHOOK RECEIVER (POST)
# --------------------

@patch("instagram_bot_graphs_api.api_create_user")
@patch("instagram_bot_graphs_api.send_dm")
def test_webhook_tracker_message(mock_send_dm, mock_create_user):
    payload = {
        "entry": [
            {
                "messaging": [
                    {
                        "sender": {"id": "987654321"},
                        "message": {"text": "Трекер"},
                    }
                ]
            }
        ]
    }

    response = client.post("/webhook/instagram", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    mock_create_user.assert_called_once_with("ig_987654321")
    mock_send_dm.assert_called_once()

    args, kwargs = mock_send_dm.call_args
    assert args[0] == "987654321"
    assert "твой трекер" in args[1].lower()

# --------------------
# HEALTHCHECK
# --------------------

def test_root_healthcheck():
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "instagram webhook server is running"
    assert body["instagram_enabled"] is False
