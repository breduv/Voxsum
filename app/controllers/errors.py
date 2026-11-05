from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.methods import AnswerGuestQuery
from aiogram.types import ErrorEvent, Message
from loguru import logger

from app.core.errors import (
    EmptyRequestError,
    InvalidModelResponseError,
    ModelRateLimitError,
    ModelTimeoutError,
    ModelUnavailableError,
    TranscriptionError,
    VoiceLimitError,
)
from app.views.telegram import TelegramView


def _user_message(error: Exception) -> str:
    """Only explicitly approved messages may cross the presentation boundary."""
    if isinstance(error, EmptyRequestError):
        return "В голосовом не удалось распознать речь. Попробуй отправить другую запись."
    if isinstance(error, VoiceLimitError):
        return "Голосовое слишком большое. Лимит — 20 МиБ."
    if isinstance(error, TranscriptionError):
        return "Не удалось расшифровать голосовое. Попробуй отправить другую запись."
    if isinstance(error, ModelTimeoutError):
        return "Модель не успела ответить. Попробуй ещё раз позже."
    if isinstance(error, ModelRateLimitError):
        return "Сервис модели ограничил запросы. Попробуй ещё раз позже."
    if isinstance(error, ModelUnavailableError):
        return "Сервис модели сейчас недоступен. Попробуй позже."
    if isinstance(error, InvalidModelResponseError):
        return "Не удалось составить сводку голосового. Попробуй ещё раз позже."
    if isinstance(error, TelegramAPIError):
        return "Не удалось доставить ответ в Telegram полностью. Попробуй позже."
    return "Произошла внутренняя ошибка при обработке запроса."


async def report_request_error(
    view: TelegramView,
    message: Message | None,
    error: Exception,
    request_id: str,
    *,
    inline_message_id: str | None = None,
) -> None:
    with logger.contextualize(request_id=request_id):
        if isinstance(error, (EmptyRequestError, VoiceLimitError)):
            logger.warning("Request rejected: {}", type(error).__name__)
        else:
            logger.opt(exception=error).error("Request failed: {}", type(error).__name__)

        if message is None or isinstance(error, (TelegramForbiddenError, TelegramRetryAfter)):
            return
        if isinstance(error, TelegramAPIError) and isinstance(error.method, AnswerGuestQuery):
            return

        text = _user_message(error)
        if not isinstance(error, (EmptyRequestError, VoiceLimitError)):
            text += f"\nКод ошибки: {request_id}"
        try:
            await view.show_error(message, text, inline_message_id=inline_message_id)
        except Exception as notification_error:  # noqa: BLE001
            logger.opt(exception=notification_error).error("Error notification failed")


class ErrorController:
    def __init__(self, view: TelegramView):
        self.view = view

    async def handle(self, event: ErrorEvent) -> bool:
        message = event.update.guest_message or event.update.message
        request_id = (
            f"tg:{message.chat.id}:{message.message_id}"
            if message is not None
            else f"update:{event.update.update_id}"
        )
        await report_request_error(self.view, message, event.exception, request_id)
        return True
