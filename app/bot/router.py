from aiogram import F, Router
from aiogram.filters import Command, CommandStart

from app.controllers.commands import CommandController
from app.controllers.errors import ErrorController
from app.controllers.voice import VoiceController
from app.views.telegram import TelegramView


def setup_router(controller: VoiceController, view: TelegramView) -> Router:
    router = Router(name="voice")
    commands = CommandController(view)
    router.message.register(commands.handle_start, CommandStart())
    router.message.register(commands.handle_help, Command("help"))
    router.message.register(controller.handle_voice, F.voice)
    router.guest_message.register(controller.handle_guest_voice)
    router.errors.register(ErrorController(view).handle)
    return router
