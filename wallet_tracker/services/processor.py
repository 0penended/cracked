"""Transaction processor - handles filtering, evaluation, and alerting."""

from typing import List, Callable, Optional, Protocol
from loguru import logger

from wallet_tracker.models.domain.unified_transaction_event import UnifiedTransactionEvent, Action, SUPPORTED_ACTIONS
from wallet_tracker.db.repositories.strategies import StrategyResult
from wallet_tracker.db.repositories.transactions import TransactionsRepository
from wallet_tracker.db.repositories.strategies import StrategiesRepository
from wallet_tracker.services.utils.activity_limiter import WalletActivityLimiter


# Protocol for strategy evaluation - allows functions or classes
class StrategyEvaluator(Protocol):
    """Protocol for strategy evaluation - allows functions or classes."""

    async def __call__(
        self,
        event: UnifiedTransactionEvent,
        transaction_repo: TransactionsRepository,
    ) -> Optional[StrategyResult]:
        """Evaluate transaction and return result if strategy matches."""
        ...


# Type alias for alert decision function
AlertDecider = Callable[[List[StrategyResult]], bool]


# Protocol for alert sender
class AlertSender(Protocol):
    """Protocol for alert sender - allows different implementations."""

    async def send(
        self,
        event: UnifiedTransactionEvent,
        strategy_results: List[StrategyResult],
        transaction_value: float,
    ) -> None:
        """Send alert for the given transaction and strategy results."""
        ...


class TransactionProcessor:
    """Processes blockchain transactions: filter, save, evaluate, alert."""

    def __init__(
        self,
        transaction_repo: TransactionsRepository,
        strategies_repo: StrategiesRepository,
        strategies: List[StrategyEvaluator],
        alert_sender: AlertSender,
        should_alert: AlertDecider,
        activity_limiter: WalletActivityLimiter,
        min_transaction_value: float,
    ):
        """
        Initialize transaction processor.

        Args:
            transaction_repo: Repository for saving transactions
            strategies: List of strategy evaluators (functions or classes)
            alert_sender: Alert sender implementation
            should_alert: Function that decides if alert should be sent
            activity_limiter: Activity limiter for spam filtering
            min_transaction_value: Minimum transaction value to process
        """
        self.transaction_repo = transaction_repo
        self.strategies_repo = strategies_repo
        self.strategies = strategies
        self.alert_sender = alert_sender
        self.should_alert = should_alert
        self.activity_limiter = activity_limiter
        self.min_transaction_value = min_transaction_value

    def _round_value(self, value: float) -> float:
        """Round value to 2 decimals if >= 0.01, otherwise return as-is."""
        if value >= 0.01:
            return round(value, 2)
        return value

    def _get_transaction_type(self, event: UnifiedTransactionEvent) -> str:
        """Get human-readable transaction type."""
        action_map = {
            Action.BUY: "BUY",
            Action.SELL: "SELL",
            Action.OPEN_LONG: "OPEN LONG",
            Action.CLOSE_LONG: "CLOSE LONG",
            Action.OPEN_SHORT: "OPEN SHORT",
            Action.CLOSE_SHORT: "CLOSE SHORT",
        }
        return action_map.get(event.action, event.action.value)

    def _get_token_type(self, event: UnifiedTransactionEvent) -> str:
        """Get the token type based on the action."""
        # Actions where we receive the token (not USDC)
        if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
            return event.received_token_symbol
        else:
            return event.spent_token_symbol

    async def process(self, event: UnifiedTransactionEvent) -> None:
        """
        Process a blockchain transaction event.

        Flow:
        1. Filter by activity (spam prevention)
        2. Filter by transaction value
        3. Save transaction to database
        4. Evaluate all strategies
        5. Save strategy results
        6. Send alert if conditions met
        """
        try:
            # 1. Filter by activity (spam prevention)
            if self.activity_limiter.is_blacklisted(event.wallet_address):
                return

            # 2. Filter by transaction value (use event.transaction_value_usd - already rounded)
            transaction_value = event.transaction_value_usd
            if transaction_value < self.min_transaction_value:
                logger.info(
                    f"⏭️ Skipping transaction: {event.action.value} {self._get_token_type(event)} - "
                    f"value ${transaction_value:,.2f} below ${self.min_transaction_value:,.0f} threshold "
                    f"by {event.wallet_address}"
                )
                return

            # Record activity for sub-threshold transactions
            txn_value = transaction_value
            if self.activity_limiter.record_and_check(
                event.wallet_address, qualifying=txn_value < self.min_transaction_value
            ):
                logger.info(
                    f"🛑 Blacklisted wallet {event.wallet_address} due to high activity "
                    f"(> {self.activity_limiter.max_tx_per_window}/min, sub-${self.min_transaction_value:,.0f})"
                )
                return

            # Get token symbol for logging
            token_symbol = self._get_token_type(event)

            logger.info(
                f"🔄 {event.action.value} {token_symbol} ${transaction_value:,.2f} "
                f"on {event.chain} by {event.wallet_address}"
            )

            # 3. Save transaction to database
            saved_transaction = await self.transaction_repo.create_from_unified_event(
                event
            )

            # 4. Evaluate all strategies
            strategy_results = []
            for strategy in self.strategies:
                try:
                    result = await strategy(event, self.transaction_repo)
                    if result:
                        logger.info(f"✅ Strategy matched: {result.explanation}")
                        strategy_results.append(result)
                except Exception as e:
                    logger.error(f"Error evaluating strategy: {e}")

            # 5. Save strategy results if -- replace False with if the transaction is our own wallet txn so we can only save when we take a position automatically -- we want to save the stratgies we used to decide to enter
            if strategy_results and False:
                await self.strategies_repo.save_strategy_results(
                    saved_transaction.id_, strategy_results
                )

            # 6. Check if should send alert and send if needed
            if strategy_results and self.should_alert(strategy_results):
                await self.alert_sender.send(event, strategy_results, transaction_value)
                logger.info(
                    f"Alert sent for transaction {event.txn_hash} with {len(strategy_results)} strategy matches"
                )

        except Exception as e:
            # Handle duplicate key errors gracefully
            if (
                "duplicate key" in str(e).lower()
                or "unique constraint" in str(e).lower()
            ):
                logger.debug(f"Duplicate transaction {event.txn_hash}, skipping")
                return
            logger.error(f"❌ Error processing transaction {event.txn_hash}: {e}")
            raise
