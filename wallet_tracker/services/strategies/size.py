"""Size-based strategies."""

from typing import Optional
from wallet_tracker.models.domain.unified_transaction_event import UnifiedTransactionEvent, Action
from wallet_tracker.db.repositories.strategies import Strategy, StrategyResult
from wallet_tracker.db.repositories.transactions import TransactionsRepository


async def large_transaction_strategy(
    event: UnifiedTransactionEvent,
    transaction_repo: TransactionsRepository,
    threshold: float = 100000,
) -> Optional[StrategyResult]:
    """
    Strategy that identifies large transactions.
    
    Args:
        event: Transaction event to evaluate
        transaction_repo: Transaction repository (for future queries if needed)
        threshold: Minimum USD value to trigger
        
    Returns:
        StrategyResult if transaction exceeds threshold, None otherwise
    """
    # Calculate USD value based on transaction action
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

    if usd_value > threshold:
        return StrategyResult(
            strategy_id=0,  # Will be set by repository when saving
            type=Strategy.LARGE_TRANSACTION,
            explanation=f"Large transaction size: ${usd_value:,.2f} USD ({token_quantity} {token_symbol})",
            metadata={
                "usd_value": usd_value,
                "token_symbol": token_symbol,
                "token_quantity": token_quantity,
                "token_price": token_price,
                "threshold": threshold,
            },
        )

    return None

