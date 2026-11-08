from collections.abc import Iterator
from html import escape

from aiogram.types import (
    InlineQueryResultArticle,
    InputRichBlockParagraph,
    InputRichMessage,
    InputRichMessageContent,
    InputTextMessageContent,
    Message,
)
from loguru import logger

MAX_RICH_MESSAGE_BYTES = 32_768
TRANSCRIPT_TITLE = "Полная расшифровка"


def _split_message(text: str) -> Iterator[str]:
    """Split plain text at natural boundaries, within 4000 UTF-16 units."""
    while text:
        chunk = text.encode("utf-16-le")[:8000].decode("utf-16-le", errors="ignore")
        if len(chunk) < len(text):
            for separator in ("\n\n", "\n", " "):
                split_at = chunk.rfind(separator)
                if split_at >= len(chunk) // 2:
                    chunk = chunk[: split_at + len(separator)]
                    break
        yield chunk
        text = text[len(chunk) :]


def _transcript_block(transcript: str, title: str = TRANSCRIPT_TITLE) -> str:
    text = escape(transcript, quote=False).replace("\n", "<br>")
    return f"<details><summary><b>{title}</b></summary><p>{text}</p></details>"


class TelegramView:
    async def show_start(self, source: Message) -> None:
        await source.answer(
            "Привет! Я Voxsum — превращаю голосовые сообщения в краткую сводку "
            "и полную расшифровку.\n\n"
            "Пришли или перешли мне голосовое, и я расскажу, о чём в нём речь.\n\n"
            "/help — как пользоваться ботом.",
            parse_mode=None,
            direct_messages_topic_id=(
                source.direct_messages_topic.topic_id
                if source.direct_messages_topic
                else None
            ),
        )

    async def show_help(self, source: Message) -> None:
        await source.answer(
            "Как пользоваться Voxsum\n\n"
            "• В личном чате: пришли или перешли мне голосовое сообщение.\n"
            "• В другом чате: ответь на голосовое сообщением с упоминанием бота. "
            "Я пришлю результат в тот же чат.\n\n"
            "В ответе будут краткая сводка и полная расшифровка, "
            "которую можно развернуть. Каждое голосовое обрабатывается отдельно.\n\n"
            "Поддерживаются голосовые сообщения размером до 20 МБ.\n\n"
            "/start — знакомство с ботом\n"
            "/help — эта справка",
            parse_mode=None,
            direct_messages_topic_id=(
                source.direct_messages_topic.topic_id
                if source.direct_messages_topic
                else None
            ),
        )

    async def show_guest_progress(self, source: Message) -> str:
        sent = await source.answer_guest_query(
            result=InlineQueryResultArticle(
                id="voice-summary",
                title="Краткая сводка голосового",
                input_message_content=InputRichMessageContent(
                    rich_message=InputRichMessage(markdown="Готовлю сводку…"),
                ),
            ),
        )
        return sent.inline_message_id

    async def show_error(
        self, source: Message, text: str, *, inline_message_id: str | None = None
    ) -> None:
        if inline_message_id is not None:
            bot = source.bot
            if bot is None:
                raise RuntimeError("Cannot edit a response without a bot instance")
            await bot.edit_message_text(
                inline_message_id=inline_message_id,
                rich_message=InputRichMessage(blocks=[
                    InputRichBlockParagraph(text=line) for line in text.splitlines()
                ]),
            )
            return

        if source.guest_query_id:
            await source.answer_guest_query(
                result=InlineQueryResultArticle(
                    id="voice-error",
                    title="Не удалось обработать голосовое",
                    input_message_content=InputTextMessageContent(
                        message_text=text, parse_mode=None,
                    ),
                ),
            )
            return

        await source.reply(
            text,
            parse_mode=None,
            direct_messages_topic_id=(
                source.direct_messages_topic.topic_id
                if source.direct_messages_topic
                else None
            ),
        )

    async def show_answer(
        self,
        source: Message,
        summary: str,
        transcript: str,
        *,
        inline_message_id: str | None = None,
    ) -> None:
        if not summary.strip():
            raise ValueError("Cannot send an empty summary")

        bot = source.bot
        if bot is None:
            raise RuntimeError("Cannot send a response without a bot instance")

        transcript_block = _transcript_block(transcript)
        if inline_message_id is not None:
            content = f"{transcript_block}\n\n{summary}"
            if len(content.encode("utf-8")) > MAX_RICH_MESSAGE_BYTES:
                content = (
                    "Расшифровка не помещается в гостевой ответ. "
                    "Перешли голосовое боту в личный чат, чтобы получить её целиком."
                    f"\n\n{summary}"
                )
            await bot.edit_message_text(
                inline_message_id=inline_message_id,
                rich_message=InputRichMessage(markdown=content),
            )
            logger.debug("Telegram: updated guest reply with summary")
            return

        if source.guest_query_id:
            raise ValueError("Guest summaries require an inline message ID")

        summary_chunks = list(_split_message(summary))
        content = f"{transcript_block}\n\n{summary_chunks[0]}"
        fits_in_reply = len(content.encode("utf-8")) <= MAX_RICH_MESSAGE_BYTES
        if fits_in_reply:
            summary_chunks[0] = content
        messages = [InputRichMessage(markdown=chunk) for chunk in summary_chunks]
        if not fits_in_reply:
            messages.extend(
                InputRichMessage(html=_transcript_block(chunk, f"Расшифровка · часть {index}"))
                for index, chunk in enumerate(_split_message(transcript), start=1)
            )

        for index, message in enumerate(messages):
            send = source.reply_rich if index == 0 else source.answer_rich
            await send(
                rich_message=message,
                direct_messages_topic_id=(
                    source.direct_messages_topic.topic_id
                    if source.direct_messages_topic
                    else None
                ),
            )
        logger.debug("Telegram: sent {} chunks", len(messages))
