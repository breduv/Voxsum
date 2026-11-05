<div align="center">

**English** · [Русский](README.ru.md)

# Goloslov

**Short summaries of Telegram voice messages**

![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![aiogram 3.31](https://img.shields.io/badge/aiogram-3.31-2CA5E0?logo=telegram&logoColor=white)
![GigaAM v3](https://img.shields.io/badge/GigaAM-v3-6C47FF)
![LangGraph 1.2](https://img.shields.io/badge/LangGraph-1.2-1C3C3C)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

Send or forward a voice message to the bot, or mention it in a reply to a voice message.
Goloslov transcribes the recording locally and sends back a short summary in Telegram.

[Features](#features) · [Quick start](#quick-start) · [Usage](#usage) · [Configuration](#configuration)

</div>

---

## Features

| Feature | Description |
| --- | --- |
| 🎙️ **Local speech recognition** | GigaAM v3 transcribes Russian speech on the CPU, with Silero for voice activity detection. [GigaAM](https://github.com/salute-developers/GigaAM) |
| 📝 **Short summaries** | An OpenAI-compatible model turns each transcript into a Telegram Rich Message |
| 👋 **Guest Mode** | Request a summary in a supported chat without adding the bot |
| ⚡ **Model availability check** | The bot checks the configured LLM before downloading or transcribing audio |
| 🌐 **Separate proxies** | Configure connections to Telegram and the LLM API independently |
| 🐳 **Docker Compose** | The image includes FFmpeg, and a host mount keeps the model cache across container rebuilds |

## Quick start

You need Docker Compose, a Telegram bot token from BotFather, and an API compatible with OpenAI Chat Completions.

1. Copy [`.env.example`](.env.example) to `.env` and fill in the bot and model settings.

   ```dotenv
   BOT_TOKEN=your-telegram-bot-token
   API_BASE=https://your-provider.example/v1
   LLM_MODEL=your-model-id
   # Set API_KEY if your provider requires authentication.
   ```

2. In [`docker-compose.yml`](docker-compose.yml), set the host side of the model cache mount to a path on your machine. The container path is `/app/data/huggingface`.
3. Start the bot from the project root.

   ```bash
   docker compose up -d --build
   ```

Wait for `Polling started` in the logs, then send or forward a voice message to the bot.
The first startup downloads the GigaAM and Silero model files. Telegram updates arrive through long polling, so a public webhook is unnecessary.

## Usage

| What to do | Result |
| --- | --- |
| Send or forward a voice message in the bot's private chat | The bot replies to the voice message with a summary |
| Reply to a voice message with `@your_bot` in a supported chat | The bot posts **«Готовлю сводку…»** and replaces it with the summary |

### Guest Mode

Enable **Guest Mode** in the bot's settings in the BotFather Mini App.
Then open a supported chat, reply to the voice message, and send `@your_bot` using your bot's username. [Telegram Guest Bots](https://core.telegram.org/bots/features#guest-bots)

The mention by itself is enough. Extra text after the mention has no effect on the summary prompt. The guest response appears under the message that mentions the bot. [Telegram Bot API](https://core.telegram.org/bots/api#answerguestquery)

## Configuration

[`app/core/config.py`](app/core/config.py) loads settings from environment variables and `.env`.

| Variable | Required | Default | Purpose |
| --- | :---: | --- | --- |
| `BOT_TOKEN` | yes | — | Telegram bot token |
| `API_BASE` | yes | — | Provider base URL, such as `https://your-provider.example/v1` |
| `LLM_MODEL` | yes | — | Exact model ID at the provider |
| `API_KEY` | if required by the provider | — | LLM API key |
| `ASR_MODEL` | no | `gigaam-v3-e2e-rnnt` | Local speech model. Also accepts `gigaam-v3-e2e-ctc` |
| `PROXY` | no | — | Proxy for the LLM API |
| `TG_PROXY` | no | — | Proxy for the Telegram Bot API |
| `LOG_LEVEL` | no | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |

Leave unused proxies empty. With Compose, `API_BASE` must be reachable from inside the container, where `127.0.0.1` points to the bot container itself.

## Local development

Use Python 3.13 and make `ffmpeg` available on `PATH`.

<details>
<summary>Linux / macOS</summary>

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Fill in .env before starting.
python main.py
```

</details>

<details>
<summary>Windows PowerShell</summary>

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Fill in .env before starting.
.\.venv\Scripts\python.exe main.py
```

</details>

Run commands from the project root so `.env` is found. Locally, the default model cache is `data/huggingface/`.

## Operations and troubleshooting

```bash
# Follow bot logs
docker compose logs -f --tail=100 goloslov

# Rebuild after source or dependency changes
docker compose up -d --build

# Stop the bot
docker compose down
```

At `INFO`, logs show model loading and request progress. `DEBUG` adds download, transcription, and delivery details. When an error message includes a code, use it to find the corresponding `request_id` in the logs.

<details>
<summary>The container is unhealthy</summary>

The Compose health check calls `python -m app.healthcheck`, and that module is missing from the current tree. Check the logs for `Polling started` and test with a voice message. The application reads `METRICS_PORT` and `TELEGRAM_HEALTH_INTERVAL_SECONDS`, but neither setting starts a listener or a health probe in the current version.

</details>

<details>
<summary>The bot stays silent after a guest mention</summary>

Check that Guest Mode is enabled in BotFather and that the mention was sent as a reply to the voice message. With `LOG_LEVEL=INFO`, look for `Guest update received` to confirm the bot received the update.

</details>

## Project structure

```text
app/
├── agents/       # LangGraph and the summarization node
├── bot/          # Telegram update routing
├── clients/      # Local ASR and LLM API clients
├── controllers/  # Voice requests and error reporting
├── core/         # Settings, logging, and application errors
├── models/       # Transcription result type
├── services/     # Transcription and summarization
├── views/        # Telegram Rich Messages and guest replies
└── application.py

main.py           # Application entry point
docker-compose.yml
Dockerfile
```

## Privacy and limitations

- Audio is processed on the host running the bot. Temporary audio files are removed after processing.
- The LLM provider receives the transcript and a short summarization prompt. Each voice message is processed independently, without conversation history.
- The bot accepts Telegram voice messages up to 20 MiB. Summaries may omit details or reflect speech recognition errors.

---

<div align="center">

[MIT License](LICENSE)

</div>
