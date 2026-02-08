## Bot Tracker (Instagram + Telegram + FastAPI)

Проект представляет собой связку из Instagram-бота, backend API и Telegram-бота.
Используется для автоматической выдачи трекера пользователям Instagram с последующей доставкой через Telegram.

Поддерживаются два способа интеграции с Instagram:
   - через polling (instagrapi)
   - через официальный Instagram Graph API (webhook)

---

## Архитектура проекта

Проект состоит из трёх логических компонентов:

1. **Instagram-бот**

**Polling (instagrapi)**  
   - отслеживает комментарии под Reels
   - реагирует на ключевое слово («трекер»)
   - инициирует регистрацию пользователя
   - отправляет ссылку в Direct

**Webhook (Instagram Graph API)**  
   - принимает события от Meta через HTTPS webhook
   - обрабатывает входящие сообщения
   - работает без постоянного опроса Instagram
   - готов к production-использованию

2. **Backend API**

   - хранит пользователей и состояние выдачи
   - служит центральной точкой данных
   - взаимодействует с базой данных

3. **Telegram-бот**

   - принимает пользователя по deep-link
   - проверяет статус через API
   - фиксирует факт отправки трекера
   - защищает от повторной выдачи

Все компоненты связаны через HTTP-запросы.

---

## Структура проекта

```text
bot-tracker/
├── logs/                           # Логи приложения
├── tests/                          # Тесты (pytest)
│   ├── test_instagram_webhook.py
│   ├── test_instagram_bot.py
│   ├── integration/
│   └── test_full_project.py
├── telegram_bot.py                 # Telegram-бот (aiogram)
├── instagram_bot.py                # Instagram-бот (polling, instagrapi)
├── instagram_bot_graphs_api.py     # Instagram webhook (Graph API + FastAPI)
├── api_server.py                   # Backend API (FastAPI), точка взаимодействия ботов и базы данных
├── database.py                     # Работа с базой данных (SQLite)
├── logger.py                       # Настройка логирования
├── requirements.txt                # Зависимости проекта
├── .env                            # Переменные окружения
└── README.md                       # Документация проекта
```

---

## Используемые технологии

* Python 3.11
* aiogram 3 — Telegram-бот
* instagrapi - Instagram-бот
* Instagram Graph API — webhook-интеграция
* FastAPI — backend API и webhook
* SQLite — база данных
* httpx / requests — HTTP-клиенты
* python-dotenv — переменные окружения
* pytest — тестирование
* logging — логирование
* Cloudflare Tunnel — HTTPS-доступ для webhook

---

## База данных

База данных реализована на SQLite.

Файл:

```
database.py
```

Таблица users содержит:

* instagram_username
* telegram_user_id
* is_subscribed
* tracker_sent_at
* logs

Инициализация БД:

```
python database.py
```

---

## Instagram (polling-бот)

Файл:

```
instagram_bot.py
```

Задачи:

* отслеживание комментариев под Reels
* реакция на ключевое слово
* регистрация пользователя через API
* отправка ссылки в Direct (deep-link в Telegram)

⚠️ В реальных условиях Instagram может ограничивать активность ботов. 
Проект тестируется через mock-тесты и изолированные сценарии.

---

## Instagram (webhook, Graph API)

Файл:

```
instagram_bot_graphs_api.py
```

Задачи:

* приём webhook-событий от Meta
* верификация webhook (hub.challenge)
* обработка входящих сообщений
* отправка DM через Graph API (или mock-режим). Позволяет тестировать webhook без реального Instagram-токена
* интеграция с backend API

Webhook работает через HTTPS (например, Cloudflare Tunnel) и готов к production-сценариям.

---

## Telegram-бот

Файл:

```
telegram_bot.py
```

Логика:

* обработка /start
* поддержка deep-link вида insta_
* проверка пользователя через API
* фиксация отправки трекера
* защита от повторной выдачи

---

## Переменные окружения

Необходимо создать файл .env:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_BOT_LINK=https://t.me/your_bot

# Backend API
API_BASE_URL=http://localhost:8000

# Instagram (polling)
INSTAGRAM_USERNAME=your_account_username
INSTAGRAM_PASSWORD=your_account_password

# Instagram (webhook)
IG_VERIFY_TOKEN=your_verify_token
IG_PAGE_ACCESS_TOKEN=optional_for_dev

# Прочее
TARGET_REELS_ID=your_reels_id
```

---

## Запуск проекта

1. Установка зависимостей

```
pip install -r requirements.txt
```

2. Инициализация базы данных

```
python database.py
```

3. Запуск backend API

```
uvicorn api_server:app --reload
```

4. Запуск Instagram polling-бота

```
python instagram_bot.py
```

5. Запуск Instagram webhook

```
uvicorn instagram_bot_graphs_api:app --host 0.0.0.0 --port 8000
```

5. Запуск Telegram-бота
```
python telegram_bot.py
```

---

## Тестирование

Проект покрыт unit и интеграционными тестами.

Запуск всех тестов:

```
pytest
```

Тесты проверяют:

* верификацию webhook
* обработку входящих сообщений
* взаимодействие компонентов
* обработку ошибок
* целостность сценария MVP

---

## Логирование

Централизованная настройка логгера (logger.py)
* Логи пишутся в папку logs/
* Фиксируются ключевые действия и ошибки
* Поддерживается dev и production-режим

---

## Возможные улучшения

* Полный переход на webhook
* Named Cloudflare Tunnel
* Docker-контейнеризация
* Retry-механизмы
* Асинхронные HTTP-клиенты
* CI/CD
* Расширение тестового покрытия

---

## Статус проекта

MVP готов и полностью покрыт тестами.
Архитектура поддерживает webhook-интеграцию и готова к масштабированию и production-нагрузке.