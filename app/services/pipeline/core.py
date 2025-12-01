from typing import List
from loguru import logger

from app.models.domain.blockchain import UnifiedTransactionEvent
from app.services.routers.base import TransactionStrategy, AlertRouter, AlertTrigger
from app.db.repositories.transactions import TransactionsRepository
from app.db.repositories.strategies import StrategiesRepository


class CoreTransactionPipeline:
    """Core pipeline for processing blockchain transactions."""

    def __init__(
        self,
        strategies: List[TransactionStrategy],
        alert_router: AlertRouter,
        alert_trigger: AlertTrigger,
        strategies_repository: StrategiesRepository,
        transaction_repository: TransactionsRepository,
    ):
        self.strategies = strategies
        self.alert_router = alert_router
        self.alert_trigger = alert_trigger
        self.strategies_repository = strategies_repository
        self.transaction_repository = transaction_repository

    def _get_transaction_type(self, event: UnifiedTransactionEvent) -> str:
        """Get human-readable transaction type."""
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
        return action_map.get(event.action.value, event.action.value)

    def _get_token_type(self, event: UnifiedTransactionEvent) -> str:
        """Get the token type based on the action."""
        if event.action.value in ["BUY", "OPEN_LONG", "CLOSE_SHORT", "SHORT_TO_LONG"]:
            # For buy/long actions, show the token being received
            return event.received_token_symbol
        else:
            # For sell/short actions, show the token being spent
            return event.spent_token_symbol

    def _get_transaction_value(self, event: UnifiedTransactionEvent) -> float:
        """Get the transaction value in USD."""
        if event.action.value in ["BUY", "OPEN_LONG", "CLOSE_SHORT", "SHORT_TO_LONG"]:
            # For buy/long actions, use the spent amount (USD spent)
            return round(event.spent_token_amount * event.spent_token_price, 2)
        else:
            # For sell/short actions, use the received amount (USD received)
            return round(event.received_token_quantity * event.received_token_price, 2)

    async def handle_event(self, event: UnifiedTransactionEvent) -> None:
        """Process a blockchain transaction event."""
        try:
            # Get transaction value for filtering
            transaction_value = self._get_transaction_value(event)

            # Skip transactions under $1000
            if transaction_value < 1000:
                logger.info(
                    f"⏭️ Skipping transaction: {event.action.value} {self._get_token_type(event)} - value ${transaction_value:,.2f} below $1,000 threshold by {event.wallet_address}"
                )
                return

            # Get token symbol based on action
            token_symbol = (
                event.received_token_symbol
                if event.action.value
                in ["BUY", "OPEN_LONG", "CLOSE_SHORT", "SHORT_TO_LONG"]
                else event.spent_token_symbol
            )

            logger.info(
                f"🔄 {event.action.value} {token_symbol} ${transaction_value:,.2f} on {event.chain} by {event.wallet_address}"
            )
            saved_transaction = (
                await self.transaction_repository.create_from_unified_event(event)
            )

            # Evaluate all strategies
            strategy_results = []
            for strategy in self.strategies:
                try:
                    result = await strategy.evaluate(event)
                    if result:
                        logger.info(
                            f"✅ Strategy {strategy.description} matched with confidence {result.confidence}: ${result.explanation}"
                        )
                        strategy_results.append(result)
                except Exception as e:
                    logger.error(
                        f"Error evaluating strategy {strategy.description}: {e}"
                    )

            # Save strategy results
            if strategy_results:
                await self.strategies_repository.save_strategy_results(
                    saved_transaction.id_, strategy_results
                )

            # Check if we should send an alert based on the alert trigger
            if strategy_results and self.alert_trigger.should_alert(strategy_results):
                # Extract transaction details for the alert
                transaction_type = self._get_transaction_type(event)
                token_type = self._get_token_type(event)

                await self.alert_router.send(
                    strategy_results,
                    event.wallet_address,
                    transaction_type,
                    transaction_value,
                    token_type,
                )
                logger.info(
                    f"Alert sent for transaction {event.txn_hash} with {len(strategy_results)} strategy matches"
                )

        except Exception as e:
            logger.error(f"❌ Error processing transaction {event.txn_hash}: {e}")
            raise
