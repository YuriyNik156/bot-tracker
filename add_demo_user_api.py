import requests

API_BASE_URL = "http://localhost:8000"

response = requests.post(
    f"{API_BASE_URL}/users",
    json={"instagram_username": "demo_user"},
    timeout=5
)

print(response.status_code, response.text)
