from aiogram.types import Message

from app.views.telegram import TelegramView


class CommandController:
    def __init__(self, view: TelegramView):
        self.view = view

    async def handle_start(self, message: Message) -> None:
        await self.view.show_start(message)

    async def handle_help(self, message: Message) -> None:
        await self.view.show_help(message)
