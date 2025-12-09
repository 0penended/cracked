"""Simple alert sending interface."""

from typing import List
from loguru import logger

from wallet_tracker.models.domain.unified_transaction_event import UnifiedTransactionEvent
from wallet_tracker.db.repositories.strategies import StrategyResult
from wallet_tracker.services.processor import AlertSender
from wallet_tracker.clients.TelegramClient import TelegramClient


class TelegramAlertSender(AlertSender):
    """Simple Telegram alert sender."""

    def __init__(
        self,
        telegram_client: TelegramClient,
        chat_id: str,
        chain_name: str = "Unknown",
    ):
        """
        Initialize Telegram alert sender.
        
        Args:
            telegram_client: Telegram client instance
            chat_id: Telegram chat ID to send alerts to
            chain_name: Name of the blockchain (for display)
        """
        self.telegram_client = telegram_client
        self.chat_id = chat_id
        self.chain_name = chain_name

    async def send(
        self,
        event: UnifiedTransactionEvent,
        strategy_results: List[StrategyResult],
        transaction_value: float,
    ) -> None:
        """Send alert to Telegram."""
        if not self.telegram_client or not self.chat_id:
            logger.warning("Telegram configuration missing, skipping alert")
            return

        # Build message
        message = self._build_message(
            event,
            strategy_results,
            transaction_value,
        )

        # Send to Telegram
        await self.telegram_client.send_message_async(
            message, self.chat_id, parse_mode="Markdown"
        )

    def _build_message(
        self,
        event: UnifiedTransactionEvent,
        strategy_results: List[StrategyResult],
        transaction_value: float,
    ) -> str:
        """Build alert message for Telegram."""
        # Get transaction type
        action_map = {
            "BUY": "BUY",
            "SELL": "SELL",
            "OPEN_LONG": "OPEN LONG",
            "CLOSE_LONG": "CLOSE LONG",
            "OPEN_SHORT": "OPEN SHORT",
            "CLOSE_SHORT": "CLOSE SHORT",
            "LONG_TO_SHORT": "LONG > SHORT",
            "SHORT_TO_LONG": "SHORT > LONG",
        }
        transaction_type = action_map.get(event.action.value, event.action.value)

        # Get token type
        if event.action.value in ["BUY", "OPEN_LONG", "CLOSE_SHORT", "SHORT_TO_LONG"]:
            token_type = event.received_token_symbol
        else:
            token_type = event.spent_token_symbol

        # Truncate wallet address for readability
        short_wallet = event.wallet_address[:10] + "..." + event.wallet_address[-6:]

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

