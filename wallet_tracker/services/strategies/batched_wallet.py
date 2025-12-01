"""Batched wallet strategy."""

from typing import Optional, Dict
from wallet_tracker.models.domain.unified_transaction_event import UnifiedTransactionEvent, Action
from wallet_tracker.db.repositories.strategies import Strategy, StrategyResult
from wallet_tracker.db.repositories.transactions import TransactionsRepository


class BatchedWalletStrategy:
    """Strategy that tracks batched transactions from different wallets."""

    def __init__(
        self,
        batch_threshold: int = 5,
        time_window: int = 1800,
    ):
        """
        Initialize batched wallet strategy.
        
        Args:
            batch_threshold: Minimum number of unique wallets to trigger
            time_window: Time window in seconds
        """
        self.batch_threshold = batch_threshold
        self.time_window = time_window
        # Track by token identifier (ID or symbol) and action
        self.token_action_transactions: Dict[str, list] = {}

    async def __call__(
        self,
        event: UnifiedTransactionEvent,
        transaction_repo: TransactionsRepository,
    ) -> Optional[StrategyResult]:
        """Evaluate if transaction is part of a batched wallet activity."""
        current_time = event.timestamp // 1000  # Convert to seconds

        # Determine token identifier
        if event.action in [Action.BUY, Action.OPEN_LONG]:
            token_identifier = event.received_token_id or event.received_token_symbol
        elif event.action in [
            Action.SELL,
            Action.CLOSE_LONG,
            Action.OPEN_SHORT,
            Action.CLOSE_SHORT,
        ]:
            token_identifier = event.spent_token_id or event.spent_token_symbol
        else:
            token_identifier = event.received_token_id or event.received_token_symbol

        # Create key for tracking: token_identifier + action
        tracking_key = f"{token_identifier}_{event.action.value}"

        # Initialize tracking if not exists
        if tracking_key not in self.token_action_transactions:
            self.token_action_transactions[tracking_key] = []

        # Add current transaction with wallet info
        self.token_action_transactions[tracking_key].append(
            {
                "wallet": event.wallet_address,
                "timestamp": current_time,
                "tx_hash": event.txn_hash,
            }
        )

        # Remove old transactions outside time window
        self.token_action_transactions[tracking_key] = [
            t
            for t in self.token_action_transactions[tracking_key]
            if current_time - t["timestamp"] < self.time_window
        ]

        # Get unique wallets for this token-action combination
        unique_wallets = set(
            t["wallet"] for t in self.token_action_transactions[tracking_key]
        )

        # Check if threshold exceeded
        if len(unique_wallets) >= self.batch_threshold:
            # Calculate USD value for the transaction
            if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
                usd_value = event.received_token_quantity * event.received_token_price
                token_symbol = event.received_token_symbol
                token_quantity = event.received_token_quantity
                token_price = event.received_token_price
            elif event.action in [Action.SELL, Action.CLOSE_LONG, Action.OPEN_SHORT]:
                usd_value = event.spent_token_amount * event.spent_token_price
                token_symbol = event.spent_token_symbol
                token_quantity = event.spent_token_amount
                token_price = event.spent_token_price
            else:
                usd_value = event.received_token_quantity * event.received_token_price
                token_symbol = event.received_token_symbol
                token_quantity = event.received_token_quantity
                token_price = event.received_token_price

            return StrategyResult(
                strategy_id=0,  # Will be set by repository when saving
                type=Strategy.BATCHED_WALLET,
                explanation=f"Multiple wallets ({len(unique_wallets)}) performing {event.action.value} on {token_identifier} in {self.time_window}s",
                metadata={
                    "unique_wallets": len(unique_wallets),
                    "action": event.action.value,
                    "token_identifier": token_identifier,
                    "time_window": self.time_window,
                    "threshold": self.batch_threshold,
                    "wallet_addresses": list(unique_wallets),
                    "usd_value": usd_value,
                    "token_symbol": token_symbol,
                    "token_quantity": token_quantity,
                    "token_price": token_price,
                },
            )

        return None

