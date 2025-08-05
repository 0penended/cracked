from typing import List
from app.services.routers.base import AlertRouter, StrategyResult
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

    async def send(self, strategy_results: List[StrategyResult]):
        """Send alert to Telegram."""
        if not self.telegram_client or not self.chat_id:
            print("Telegram configuration missing")
            return

        # Build message
        message = self._build_message(strategy_results)

        # Send to Telegram
        await self.telegram_client.send_message_async(
            message, self.chat_id, parse_mode="Markdown"
        )

    def _build_message(self, strategy_results: List[StrategyResult]) -> str:
        """Build alert message for Telegram."""
        # Get the first strategy result to extract transaction info
        # Note: All strategy results should be from the same transaction
        if not strategy_results:
            return "No strategy results to display"

        # Extract transaction info from the first result's metadata
        first_result = strategy_results[0]

        # Try to get transaction info from metadata
        metadata = first_result.metadata or {}

        # Extract USD value and token info from metadata
        usd_value = metadata.get("usd_value", 0)
        token_symbol = metadata.get("token_symbol", "Unknown")
        token_quantity = metadata.get("token_quantity", 0)
        token_price = metadata.get("token_price", 0)

        # If metadata doesn't have the info, we can't display it properly
        if not all([usd_value, token_symbol, token_quantity, token_price]):
            message = f"🚨 {self.chain_name.upper()} ALERT 🚨\n\n"
            message += f"💰 **Transaction Value**: ${usd_value:,.2f} USD\n"
            message += f"📊 **Amount**: {token_quantity:,.4f} {token_symbol}\n"
            message += f"💵 **Price**: ${token_price:,.6f} USD\n"
        else:
            message = f"🚨 {self.chain_name.upper()} ALERT 🚨\n\n"
            message += f"💰 **Transaction Value**: ${usd_value:,.2f} USD\n"
            message += f"📊 **Amount**: {token_quantity:,.4f} {token_symbol}\n"
            message += f"💵 **Price**: ${token_price:,.6f} USD\n"

        message += f"\n🎯 **Triggers**:\n"
        for i, result in enumerate(strategy_results, 1):
            confidence_pct = result.confidence * 100
            message += f"{i}. {result.type.value.replace('_', ' ').title()} ({confidence_pct:.1f}%) - {result.explanation}\n"

        return message
