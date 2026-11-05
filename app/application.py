import asyncio
from time import perf_counter

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from loguru import logger

from app.agents.graph import build_graph
from app.bot.router import setup_router
from app.clients.asr import ASR
from app.clients.llm import create_llm
from app.controllers.voice import VoiceController
from app.core.config import Settings
from app.services.chat import ChatService
from app.services.transcription import TranscriptionService
from app.views.telegram import TelegramView


def _create_bot(settings: Settings) -> Bot:
    session = AiohttpSession(
        proxy=settings.tg_proxy.get_secret_value() if settings.tg_proxy else None
    )
    return Bot(token=settings.bot_token.get_secret_value(), session=session)


def _create_dispatcher(controller: VoiceController, view: TelegramView) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(setup_router(controller=controller, view=view))
    return dispatcher


async def run_application(settings: Settings) -> None:
    """Build the ASR → LLM pipeline and own its lifecycle during polling."""
    logger.info("Starting bot: ASR={}, LLM={}", settings.asr_model, settings.llm_model)

    try:
        started = perf_counter()
        logger.info("ASR: loading model")
        asr = await asyncio.to_thread(ASR, settings.asr_model)
        logger.info("ASR: ready ({:.1f}s)", perf_counter() - started)

        async with create_llm(settings) as model:
            view = TelegramView()
            controller = VoiceController(
                transcription=TranscriptionService(asr),
                chat=ChatService(build_graph(model), model),
                view=view,
            )
            dispatcher = _create_dispatcher(controller, view)

            async with _create_bot(settings).context() as bot:
                allowed_updates = dispatcher.resolve_used_update_types()
                await bot.delete_my_commands()
                logger.info("Polling started")
                await dispatcher.start_polling(
                    bot,
                    allowed_updates=allowed_updates,
                    close_bot_session=False,
                )
    finally:
        logger.info("Application stopped")
