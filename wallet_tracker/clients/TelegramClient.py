import logging
from telegram import Bot
from telegram.error import TelegramError


class TelegramClient:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)

    async def send_message_async(self, message: str, chat_id: str, **kwargs) -> None:
        """Asynchronous method to send a message."""
        try:
            await self.bot.send_message(chat_id=chat_id, text=message, **kwargs)
        except TelegramError as e:
            logging.error(f"Telegram message error: {e}")
