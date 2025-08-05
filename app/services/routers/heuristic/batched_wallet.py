from typing import Dict
from app.services.routers.base import TransactionStrategy, StrategyResult
from app.models.domain.blockchain import UnifiedTransactionEvent, Action
from app.models.domain.transactions import Strategy


class BatchedWalletStrategy(TransactionStrategy):
    """Strategy that tracks batched transactions from different wallets with the same action for the same token."""

    def __init__(
        self, batch_threshold: int = 5, time_window: int = 1800, strategy_id: int = None
    ):
        super().__init__(strategy_id=strategy_id)
        self.batch_threshold = batch_threshold
        self.time_window = time_window  # seconds
        # Track by token identifier (ID or symbol) and action
        self.token_action_transactions: Dict[str, list] = {}

    @property
    def type(self) -> Strategy:
        return Strategy.BATCHED_WALLET

    @property
    def description(self) -> str:
        return (
            f"Batched Wallet ({self.batch_threshold}+ wallets in {self.time_window}s)"
        )

    async def evaluate(self, event: UnifiedTransactionEvent) -> StrategyResult:
        current_time = event.timestamp // 1000  # Convert to seconds

        # Determine token identifier - prefer token ID, fallback to symbol
        token_identifier = None
        if event.action in [Action.BUY, Action.OPEN_LONG]:
            # For buy actions, track the received token
            token_identifier = event.received_token_id or event.received_token_symbol
        elif event.action in [
            Action.SELL,
            Action.CLOSE_LONG,
            Action.OPEN_SHORT,
            Action.CLOSE_SHORT,
        ]:
            # For sell actions, track the spent token
            token_identifier = event.spent_token_id or event.spent_token_symbol
        else:
            # For SWAP actions, track the received token
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
            confidence = min(1.0, (len(unique_wallets) / self.batch_threshold) * 0.4)

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
                strategy_id=self.strategy_id,
                type=self.type,
                confidence=confidence,
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
