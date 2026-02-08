## Bot Tracker (Instagram + Telegram + FastAPI)

Проект представляет собой связку из Instagram-бота, backend API и Telegram-бота.
Используется для автоматической выдачи трекера пользователям Instagram с последующей доставкой через Telegram.

---

## Архитектура проекта

Проект состоит из трёх логических компонентов:

1. **Instagram-бот**

   - отслеживает комментарии под Reels
   - реагирует на ключевое слово («трекер»)
   - инициирует регистрацию пользователя

2. **Backend API**

   - хранит пользователей и состояние выдачи
   - служит центральной точкой данных
   - взаимодействует с базой данных

3. **Telegram-бот**

   - принимает пользователя по deep-link
   - проверяет статус через API
   - фиксирует факт отправки трекера

Все компоненты связаны через HTTP-запросы.

---

## Структура проекта

```text
bot-tracker/
├── logs/                   # Логи приложения
├── tests/                  # Тесты (pytest)
│   └── test_full_project.py
├── telegram_bot.py         # Telegram-бот (aiogram)
├── instagram_bot.py        # Instagram-бот (Reels / комментарии)
├── api_server.py           # Backend API (FastAPI), точка взаимодействия ботов и базы данных
├── database.py             # Работа с базой данных (SQLite)
├── logger.py               # Настройка логирования
├── requirements.txt        # Зависимости проекта
├── .env                    # Переменные окружения
└── README.md               # Документация проекта
```

---

## Используемые технологии

* Python 3.11
* aiogram 3 — Telegram-бот
* instagrapi - Instagram-бот
* FastAPI — backend API
* SQLite — база данных
* httpx / requests — HTTP-клиенты
* python-dotenv — переменные окружения
* pytest — тестирование
* logging — логирование

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

## Instagram-бот

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

TELEGRAM_BOT_TOKEN=your_telegram_bot_token 
API_BASE_URL=http://localhost:8000

INSTAGRAM_USERNAME=your_account_username 
INSTAGRAM_PASSWORD=your_account_password 
TELEGRAM_BOT_LINK=https://t.me/instagram_tele_tracker_bot 
TARGET_REELS_ID=your_reels_id

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
uvicorn app.main:app --reload
```

4. Запуск Instagram-бота

```
python instagram_bot.py
```

5. Запуск Telegram-бота
```
python telegram_bot.py
```

---

## Тестирование

Проект покрыт интеграционными mock-тестами.

Запуск всех тестов:

```
pytest
```

Тесты проверяют:

* взаимодействие компонентов
* корректность логики защиты
* обработку ошибок
* целостность сценария MVP

---

## Логирование

* Централизованная настройка логгера (logger.py)
* Логи пишутся в папку logs/
* Фиксируются ключевые действия и ошибки

---

## Возможные улучшения

* Webhook вместо polling
* Docker-контейнеризация
* Асинхронные клиенты повсюду
* Retry-механизмы
* CI/CD
* Расширение тестового покрытия

---

## Статус проекта

MVP готов. 
Архитектура протестирована через mock-тесты и готова к масштабированию.