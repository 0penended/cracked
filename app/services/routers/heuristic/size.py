from app.services.routers.base import HeuristicRouter, AlertResult
from app.models.domain.blockchain import UnifiedTransactionEvent, Action


class SizeRouter(HeuristicRouter):
    """Router that triggers on unusual transaction sizes."""

    def __init__(self, size_threshold: float = 10000):
        self.size_threshold = size_threshold

    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        # Calculate USD value based on transaction action
        if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
            # For buys, use received token value
            usd_value = event.recieved_token_quantity * event.recieved_token_price
            token_symbol = event.recieved_token_symbol
            token_quantity = event.recieved_token_quantity
        elif event.action in [Action.SELL, Action.CLOSE_LONG, Action.OPEN_SHORT]:
            # For sells, use spent token value
            usd_value = event.spent_token_amount * event.spent_token_price
            token_symbol = event.spent_token_symbol
            token_quantity = event.spent_token_amount
        else:
            # For other actions (SWAP, LIQUIDATION), default to received side
            usd_value = event.recieved_token_quantity * event.recieved_token_price
            token_symbol = event.recieved_token_symbol
            token_quantity = event.recieved_token_quantity

        if usd_value > self.size_threshold:
            return AlertResult(
                triggered=True,
                score=1,
                explanation=f"Large transaction size: ${usd_value:,.2f} USD ({token_quantity} {token_symbol})",
            )
        return AlertResult(triggered=False, score=0.0)
