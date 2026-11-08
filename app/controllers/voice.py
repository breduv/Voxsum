from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from aiogram import Bot
from aiogram.types import Message, Voice
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger

from app.controllers.errors import report_request_error
from app.core.errors import VoiceLimitError
from app.services.chat import ChatService
from app.services.transcription import TranscriptionService
from app.views.telegram import TelegramView

MAX_VOICE_BYTES = 20 * 1024 * 1024


class VoiceController:
    def __init__(
        self,
        transcription: TranscriptionService,
        chat: ChatService,
        view: TelegramView,
    ):
        self.transcription = transcription
        self.chat = chat
        self.view = view

    async def handle_voice(self, message: Message) -> None:
        voice = message.voice
        if voice is None or message.bot is None:
            return

        started = perf_counter()
        request_id = f"tg:{message.chat.id}:{message.message_id}"
        with logger.contextualize(request_id=request_id):
            logger.info("Request started: voice ({}s)", voice.duration)
            if voice.file_size is not None and voice.file_size > MAX_VOICE_BYTES:
                raise VoiceLimitError("Voice file exceeds 20 MiB")

            async with ChatActionSender.typing(
                chat_id=message.chat.id,
                bot=message.bot,
                message_thread_id=(
                    message.message_thread_id if message.is_topic_message else None
                ),
            ):
                summary, transcript = await self._summarize_voice(message.bot, voice)
                logger.debug("Delivering summary")
                await self.view.show_answer(message, summary, transcript)
            logger.info("Request delivered ({:.1f}s)", perf_counter() - started)

    async def handle_guest_voice(self, message: Message) -> None:
        started = perf_counter()
        request_id = f"tg:{message.chat.id}:{message.message_id}"
        replied_message = message.reply_to_message
        with logger.contextualize(request_id=request_id):
            logger.info(
                "Guest update received: query_present={}, voice_present={}, reply_present={}",
                bool(message.guest_query_id),
                message.voice is not None,
                replied_message is not None,
            )
            if not message.guest_query_id or message.bot is None:
                logger.warning("Guest update ignored: missing query ID or bot context")
                return

            voice = message.voice or (replied_message.voice if replied_message else None)
            if voice is None:
                reply_author = replied_message.from_user if replied_message else None
                if reply_author is not None and reply_author.id == message.bot.id:
                    return

                username = (await message.bot.me()).username
                mention = f"@{username}" if username else "упоминанием бота"
                await self.view.show_error(
                    message,
                    f"Ответь на голосовое сообщением с {mention}, чтобы получить краткую сводку.",
                )
                return

            logger.info("Request started: guest voice ({}s)", voice.duration)
            inline_message_id = await self.view.show_guest_progress(message)
            try:
                summary, transcript = await self._summarize_voice(message.bot, voice)
                await self.view.show_answer(
                    message, summary, transcript, inline_message_id=inline_message_id
                )
            except Exception as error:  # noqa: BLE001
                await report_request_error(
                    self.view, message, error, request_id,
                    inline_message_id=inline_message_id,
                )
                return
            logger.info("Request delivered ({:.1f}s)", perf_counter() - started)

    async def _summarize_voice(self, bot: Bot, voice: Voice) -> tuple[str, str]:
        if voice.file_size is not None and voice.file_size > MAX_VOICE_BYTES:
            raise VoiceLimitError("Voice file exceeds 20 MiB")

        await self.chat.ensure_available()

        with TemporaryDirectory(prefix="voxsum-voice-") as directory:
            audio_path = Path(directory) / "voice.ogg"
            logger.debug("Voice: downloading")
            await bot.download(voice, destination=audio_path, timeout=120)
            if audio_path.stat().st_size > MAX_VOICE_BYTES:
                raise VoiceLimitError("Voice file exceeds 20 MiB")
            logger.debug("Voice: download completed")
            transcript = await self.transcription.transcribe(audio_path)

        summary = await self.chat.summarize(transcript.text)
        return summary, transcript.text
