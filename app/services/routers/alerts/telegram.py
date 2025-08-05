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

    async def send(
        self,
        strategy_results: List[StrategyResult],
        wallet_address: str,
        transaction_type: str,
        transaction_value: float,
        token_type: str,
    ):
        """Send alert to Telegram."""
        if not self.telegram_client or not self.chat_id:
            print("Telegram configuration missing")
            return

        # Build message
        message = self._build_message(
            strategy_results,
            wallet_address,
            transaction_type,
            transaction_value,
            token_type,
        )

        # Send to Telegram
        await self.telegram_client.send_message_async(
            message, self.chat_id, parse_mode="Markdown"
        )

    def _build_message(
        self,
        strategy_results: List[StrategyResult],
        wallet_address: str,
        transaction_type: str,
        transaction_value: float,
        token_type: str,
    ) -> str:
        """Build alert message for Telegram."""
        if not strategy_results:
            return "No strategy results to display"

        # Truncate wallet address for readability
        short_wallet = wallet_address[:10] + "..." + wallet_address[-6:]

        # Build the message
        message = f"🚨 {self.chain_name.upper()} ALERT 🚨\n\n"
        message += f"💰 Transaction Value: ${transaction_value:,.2f} USD\n"
        message += f"📊 Type: {transaction_type}\n"
        message += f"🪙 Token: {token_type}\n"
        message += f"👤 Wallet: {short_wallet}\n"

        message += f"\n🎯 Triggers:\n"
        for i, result in enumerate(strategy_results, 1):
            strategy_name = result.type.value.replace("_", " ").title()
            message += f"{i}. {strategy_name}\n"

        return message
