"""Volume-based strategies."""

from typing import Optional
from wallet_tracker.models.domain.unified_transaction_event import UnifiedTransactionEvent, Action
from wallet_tracker.db.repositories.strategies import Strategy, StrategyResult
from wallet_tracker.db.repositories.transactions import TransactionsRepository


async def high_volume_strategy(
    event: UnifiedTransactionEvent,
    transaction_repo: TransactionsRepository,
    threshold: float = 1000000,
) -> Optional[StrategyResult]:
    """
    Strategy that identifies high volume transactions.
    
    Args:
        event: Transaction event to evaluate
        transaction_repo: Transaction repository (for future queries if needed)
        threshold: Minimum 24h volume to trigger
        
    Returns:
        StrategyResult if transaction volume exceeds threshold, None otherwise
    """
    # Get the appropriate volume to check based on the transaction action
    volume_to_check = _get_volume_for_action(event)

    if volume_to_check > threshold:
        action_name = event.action.value

        return StrategyResult(
            strategy_id=0,  # Will be set by repository when saving
            type=Strategy.HIGH_VOLUME,
            explanation=f"High volume {action_name} transaction: {volume_to_check:,.0f}",
            metadata={
                "volume": volume_to_check,
                "action": action_name,
                "threshold": threshold,
                "usd_value": volume_to_check,  # For volume strategies, volume is the USD value
                "token_symbol": (
                    event.received_token_symbol
                    if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]
                    else event.spent_token_symbol
                ),
                "token_quantity": (
                    event.received_token_quantity
                    if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]
                    else event.spent_token_amount
                ),
                "token_price": (
                    event.received_token_price
                    if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]
                    else event.spent_token_price
                ),
            },
        )

    return None


def _get_volume_for_action(event: UnifiedTransactionEvent) -> float:
    """Get the appropriate volume to check based on the transaction action."""
    # For all actions, we want to check the non-USD token volume
    # USD is typically the collateral, so we check the actual asset volume

    # Actions where we're receiving the asset (not USD)
    if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
        # Use received token volume (the asset we're acquiring)
        return event.received_token_volume_h24

    # Actions where we're spending the asset (not USD)
    elif event.action in [Action.SELL, Action.OPEN_SHORT, Action.CLOSE_LONG]:
        # Use spent token volume (the asset we're disposing)
        return event.spent_token_volume_h24

    # For SWAP actions, use the higher volume between received and spent
    # (excluding USD if it's one of the tokens)
    elif event.action == Action.SWAP:
        received_volume = event.received_token_volume_h24
        spent_volume = event.spent_token_volume_h24

        # If one of the tokens is USD, use the other token's volume
        if event.received_token_symbol in ["USD", "USDC"]:
            return spent_volume
        elif event.spent_token_symbol in ["USD", "USDC"]:
            return received_volume
        else:
            # Both are non-USD tokens, use the higher volume
            return max(received_volume, spent_volume)

    # Default fallback
    else:
        return max(event.received_token_volume_h24, event.spent_token_volume_h24)

