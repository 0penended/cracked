from typing import Dict, Any
from app.services.routers.base import AlertRouter, AlertResult
from app.models.domain.blockchain import UnifiedTransactionEvent, Action
from app.clients.TelegramClient import TelegramClient


class TelegramAlertRouter(AlertRouter):
    """Router that sends alerts to Telegram."""

    def __init__(
        self, telegram_client: TelegramClient, chat_id: str, chain_name: str = "Unknown"
    ):
        self.telegram_client = telegram_client
        self.chat_id = chat_id
        self.chain_name = chain_name

    async def send(self, event: UnifiedTransactionEvent, results: list[AlertResult]):
        """Send alert to Telegram."""
        if not self.telegram_client or not self.chat_id:
            print("Telegram configuration missing")
            return

        # Build message
        message = self._build_message(event, results)

        # Send to Telegram
        await self.telegram_client.send_message_async(
            message, self.chat_id, parse_mode="Markdown"
        )

    def _build_message(
        self, event: UnifiedTransactionEvent, results: list[AlertResult]
    ) -> str:
        """Build alert message for Telegram."""
        # Calculate USD value based on transaction action
        if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
            usd_value = event.recieved_token_quantity * event.recieved_token_price
            token_symbol = event.recieved_token_symbol
            token_quantity = event.recieved_token_quantity
        elif event.action in [Action.SELL, Action.CLOSE_LONG, Action.OPEN_SHORT]:
            usd_value = event.spent_token_amount * event.spent_token_price
            token_symbol = event.spent_token_symbol
            token_quantity = event.spent_token_amount
        else:
            usd_value = event.recieved_token_quantity * event.recieved_token_price
            token_symbol = event.recieved_token_symbol
            token_quantity = event.recieved_token_quantity

        message = f"🚨 {self.chain_name.upper()} ALERT 🚨\n\n"
        message += f"💰 **Transaction Value**: ${usd_value:,.2f} USD\n"
        message += f"🔗 **Wallet**: `{event.wallet_address}`\n"
        message += f"📝 **Transaction**: `{event.txn_hash}`\n"
        message += f"⚡ **Action**: {event.action.value}\n"
        message += f"📊 **Amount**: {token_quantity:,.4f} {token_symbol}\n"
        message += f"💵 **Price**: ${event.recieved_token_price:,.6f} USD\n"

        message += f"\n🎯 **Triggers**:\n"
        for i, result in enumerate(results, 1):
            message += f"{i}. Score: {result.score:.2f} - {result.explanation}\n"

        return message
