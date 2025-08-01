from typing import Dict
from app.services.routers.base import HeuristicRouter, AlertResult
from app.models.domain.blockchain import UnifiedTransactionEvent, Action


class BatchedWalletTransactionRouter(HeuristicRouter):
    """Router that tracks batched transactions from different wallets with the same action for the same token."""

    def __init__(self, batch_threshold: int = 5, time_window: int = 300):
        self.batch_threshold = batch_threshold
        self.time_window = time_window  # seconds
        # Track by token identifier (ID or symbol) and action
        self.token_action_transactions: Dict[str, list] = {}

    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        current_time = event.timestamp // 1000  # Convert to seconds

        # Determine token identifier - prefer token ID, fallback to symbol
        token_identifier = None
        if event.action in [Action.BUY, Action.OPEN_LONG]:
            # For buy actions, track the received token
            token_identifier = event.recieved_token_id or event.recieved_token_symbol
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
            token_identifier = event.recieved_token_id or event.recieved_token_symbol

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
            return AlertResult(
                triggered=True,
                score=2,
                explanation=f"Multiple wallets ({len(unique_wallets)}) performing {event.action.value} on {token_identifier} in {self.time_window}s",
            )

        return AlertResult(triggered=False, score=0.0) 