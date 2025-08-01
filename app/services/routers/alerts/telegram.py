from typing import Dict, Any
from app.services.routers.base import AlertRouter, AlertResult
from app.models.domain.blockchain import UnifiedTransactionEvent


class TelegramAlertRouter(AlertRouter):
    """Router that sends alerts to Telegram."""

    def __init__(self, config: Dict[str, Any]):
        self.bot_token = config.get("bot_token")
        self.chat_id = config.get("chat_id")
        self.chain_name = config.get("chain_name", "Unknown")

    async def send(self, event: UnifiedTransactionEvent, results: list[AlertResult]):
        """Send alert to Telegram."""
        if not self.bot_token or not self.chat_id:
            print("Telegram configuration missing")
            return

        # Build message
        message = self._build_message(event, results)

        # Send to Telegram
        await self._send_telegram_message(message)

    def _build_message(
        self, event: UnifiedTransactionEvent, results: list[AlertResult]
    ) -> str:
        """Build alert message for Telegram."""
        message = f"🚨 {self.chain_name.upper()} ALERT 🚨\n\n"
        message += f"Wallet: `{event.wallet_address}`\n"
        message += f"Transaction: `{event.txn_hash}`\n"
        message += f"Action: {event.action}\n"
        message += f"Amount: {event.recieved_token_quantity}\n"
        if event.recieved_token_symbol:
            message += f"Symbol: {event.recieved_token_symbol}\n"
        if event.recieved_token_price:
            message += f"Price: {event.recieved_token_price}\n"

        message += f"\nTriggers:\n"
        for i, result in enumerate(results, 1):
            message += f"{i}. Score: {result.score:.2f} - {result.explanation}\n"

        return message

    async def _send_telegram_message(self, message: str):
        """Send message to Telegram."""
        try:
            import aiohttp

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        print(f"Failed to send Telegram message: {response.status}")

        except Exception as e:
            print(f"Error sending Telegram message: {e}") 