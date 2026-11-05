from collections.abc import Iterator

from aiogram.types import (
    InlineQueryResultArticle,
    InputRichBlockParagraph,
    InputRichMessage,
    InputRichMessageContent,
    InputTextMessageContent,
    Message,
)
from loguru import logger


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


class TelegramView:
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
        self, source: Message, summary: str, *, inline_message_id: str | None = None
    ) -> None:
        if not summary.strip():
            raise ValueError("Cannot send an empty summary")

        bot = source.bot
        if bot is None:
            raise RuntimeError("Cannot send a response without a bot instance")

        if inline_message_id is not None:
            await bot.edit_message_text(
                inline_message_id=inline_message_id,
                rich_message=InputRichMessage(markdown=summary),
            )
            logger.debug("Telegram: updated guest reply with summary")
            return

        if source.guest_query_id:
            raise ValueError("Guest summaries require an inline message ID")

        chunks_sent = 0
        for chunk in _split_message(summary):
            send = source.reply_rich if chunks_sent == 0 else source.answer_rich
            await send(
                rich_message=InputRichMessage(markdown=chunk),
                direct_messages_topic_id=(
                    source.direct_messages_topic.topic_id
                    if source.direct_messages_topic
                    else None
                ),
            )
            chunks_sent += 1
        logger.debug("Telegram: sent {} chunks", chunks_sent)
