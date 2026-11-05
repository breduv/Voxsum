<div align="center">

[English](README.md) · **Русский**

# Goloslov

**Краткие сводки голосовых сообщений в Telegram**

![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![aiogram 3.31](https://img.shields.io/badge/aiogram-3.31-2CA5E0?logo=telegram&logoColor=white)
![GigaAM v3](https://img.shields.io/badge/GigaAM-v3-6C47FF)
![LangGraph 1.2](https://img.shields.io/badge/LangGraph-1.2-1C3C3C)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

Отправьте или перешлите голосовое боту либо упомяните его в ответе на голосовое.
Goloslov распознает речь локально и пришлёт краткий пересказ в Telegram.

[Возможности](#возможности) · [Быстрый старт](#быстрый-старт) · [Использование](#использование) · [Настройки](#настройки)

</div>

---

## Возможности

| Возможность | Описание |
| --- | --- |
| 🎙️ **Локальное распознавание речи** | GigaAM v3 распознаёт русскую речь на CPU, а Silero выделяет участки с речью. [GigaAM](https://github.com/salute-developers/GigaAM/blob/main/README_ru.md) |
| 📝 **Краткий пересказ** | Модель через OpenAI-совместимый API составляет сводку, а бот отправляет её в формате Telegram Rich Message |
| 👋 **Гостевой режим** | Запрос сводки в поддерживаемом чате, куда бот не добавлен |
| ⚡ **Проверка доступности модели** | Бот проверяет LLM перед скачиванием и распознаванием аудио |
| 🌐 **Раздельные прокси** | Независимые настройки для Telegram и API модели |
| 🐳 **Docker Compose** | FFmpeg уже в образе, а кэш моделей сохраняется на хосте при пересборке контейнера |

## Быстрый старт

Нужны Docker Compose, токен Telegram-бота от BotFather и API, совместимый с OpenAI Chat Completions.

1. Скопируйте [`.env.example`](.env.example) в `.env` и заполните настройки бота и модели.

   ```dotenv
   BOT_TOKEN=your-telegram-bot-token
   API_BASE=https://your-provider.example/v1
   LLM_MODEL=your-model-id
   # Укажите API_KEY, если провайдер требует авторизацию.
   ```

2. В [`docker-compose.yml`](docker-compose.yml) укажите путь к кэшу моделей на своём хосте. Путь внутри контейнера — `/app/data/huggingface`.
3. Запустите бота из корня проекта.

   ```bash
   docker compose up -d --build
   ```

Дождитесь `Polling started` в логах и отправьте или перешлите боту голосовое сообщение.
При первом запуске загрузятся файлы GigaAM и Silero. Бот получает обновления через long polling, поэтому публичный вебхук не нужен.

## Использование

| Действие | Результат |
| --- | --- |
| Отправить или переслать голосовое в личный чат с ботом | Бот пришлёт сводку ответом на голосовое |
| Ответить на голосовое сообщением `@your_bot` в поддерживаемом чате | Бот отправит **«Готовлю сводку…»**, затем заменит это сообщение сводкой |

### Гостевой режим

Включите **Guest Mode** в настройках бота в мини-приложении BotFather.
В поддерживаемом чате ответьте на голосовое сообщением `@your_bot`, подставив имя своего бота. [Документация Telegram](https://core.telegram.org/bots/features#guest-bots)

Достаточно одного упоминания. Текст после него не влияет на запрос к модели. Гостевой ответ привязан к сообщению, в котором упомянули бота. [Telegram Bot API](https://core.telegram.org/bots/api#answerguestquery)

## Настройки

[`app/core/config.py`](app/core/config.py) загружает настройки из переменных окружения и `.env`.

| Переменная | Обязательна | По умолчанию | Назначение |
| --- | :---: | --- | --- |
| `BOT_TOKEN` | да | — | Токен Telegram-бота |
| `API_BASE` | да | — | Базовый URL провайдера, например `https://your-provider.example/v1` |
| `LLM_MODEL` | да | — | Точный идентификатор модели у провайдера |
| `API_KEY` | если требует провайдер | — | Ключ API модели |
| `ASR_MODEL` | нет | `gigaam-v3-e2e-rnnt` | Локальная модель распознавания. Также доступна `gigaam-v3-e2e-ctc` |
| `PROXY` | нет | — | Прокси для API модели |
| `TG_PROXY` | нет | — | Прокси для Telegram Bot API |
| `LOG_LEVEL` | нет | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` или `CRITICAL` |

Неиспользуемые прокси оставьте пустыми. При запуске через Compose адрес `API_BASE` должен быть доступен из контейнера. Адрес `127.0.0.1` внутри контейнера указывает на сам контейнер.

## Локальная разработка

Нужны Python 3.13 и `ffmpeg` в `PATH`.

<details>
<summary>Linux / macOS</summary>

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Заполните .env перед запуском.
python main.py
```

</details>

<details>
<summary>Windows PowerShell</summary>

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Заполните .env перед запуском.
.\.venv\Scripts\python.exe main.py
```

</details>

Запускайте команды из корня проекта, чтобы бот нашёл `.env`. При локальном запуске кэш моделей по умолчанию хранится в `data/huggingface/`.

## Управление и диагностика

```bash
# Следить за логами бота
docker compose logs -f --tail=100 goloslov

# Пересобрать после изменения кода или зависимостей
docker compose up -d --build

# Остановить бота
docker compose down
```

На уровне `INFO` видны загрузка моделей и ход обработки запросов. `DEBUG` добавляет детали скачивания, распознавания и отправки ответа. Если бот вернул код ошибки, по нему можно найти `request_id` в логах.

<details>
<summary>Контейнер в состоянии unhealthy</summary>

Проверка состояния в Compose вызывает `python -m app.healthcheck`, но этого модуля в текущей версии проекта нет. Проверьте наличие `Polling started` в логах и отправьте тестовое голосовое. Приложение читает `METRICS_PORT` и `TELEGRAM_HEALTH_INTERVAL_SECONDS`, но эти настройки пока не запускают сервер метрик и проверку доступности Telegram.

</details>

<details>
<summary>Бот молчит после упоминания в гостевом режиме</summary>

Проверьте, включён ли Guest Mode в BotFather и отправлено ли упоминание ответом на голосовое. При `LOG_LEVEL=INFO` запись `Guest update received` в логах подтверждает, что обновление дошло до бота.

</details>

## Структура проекта

```text
app/
├── agents/       # LangGraph и узел пересказа
├── bot/          # Маршрутизация обновлений Telegram
├── clients/      # Локальное распознавание и клиент API модели
├── controllers/  # Обработка голосовых и ошибок
├── core/         # Настройки, логирование и ошибки приложения
├── models/       # Тип результата распознавания
├── services/     # Распознавание и пересказ
├── views/        # Telegram Rich Messages и гостевые ответы
└── application.py

main.py           # Точка входа приложения
docker-compose.yml
Dockerfile
```

## Приватность и ограничения

- Аудио обрабатывается на хосте, где запущен бот. Временные аудиофайлы удаляются после обработки.
- Провайдер LLM получает расшифровку и короткую инструкцию для пересказа. Каждое голосовое обрабатывается отдельно, без истории разговора.
- Бот принимает голосовые сообщения Telegram размером до 20 МиБ. В пересказе могут пропасть детали или отразиться ошибки распознавания.

---

<div align="center">

[Лицензия MIT](LICENSE)

</div>
