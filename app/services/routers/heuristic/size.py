from app.services.routers.base import TransactionStrategy, StrategyResult
from app.models.domain.blockchain import UnifiedTransactionEvent, Action
from app.models.domain.strategy import Strategy


class LargeTransactionStrategy(TransactionStrategy):
    """Strategy that identifies large transactions."""

    def __init__(self, size_threshold: float = 10000, strategy_id: int = None):
        super().__init__(strategy_id=strategy_id)
        self.size_threshold = size_threshold

    @property
    def type(self) -> Strategy:
        return Strategy.LARGE_TRANSACTION

    @property
    def description(self) -> str:
        return f"Large Transaction (${self.size_threshold:,.0f}+)"

    async def evaluate(self, event: UnifiedTransactionEvent) -> StrategyResult:
        # Calculate USD value based on transaction action
        if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
            # For buys, use received token value
            usd_value = event.received_token_quantity * event.received_token_price
            token_symbol = event.received_token_symbol
            token_quantity = event.received_token_quantity
        elif event.action in [Action.SELL, Action.CLOSE_LONG, Action.OPEN_SHORT]:
            # For sells, use spent token value
            usd_value = event.spent_token_amount * event.spent_token_price
            token_symbol = event.spent_token_symbol
            token_quantity = event.spent_token_amount
        else:
            # For other actions (SWAP, LIQUIDATION), default to received side
            usd_value = event.received_token_quantity * event.received_token_price
            token_symbol = event.received_token_symbol
            token_quantity = event.received_token_quantity

        if usd_value > self.size_threshold:
            # Calculate confidence based on how much over threshold
            confidence = min(1.0, (usd_value / self.size_threshold) * 0.5)

            return StrategyResult(
                strategy_id=self.strategy_id,
                type=self.type,
                confidence=confidence,
                explanation=f"Large transaction size: ${usd_value:,.2f} USD ({token_quantity} {token_symbol})",
                metadata={
                    "usd_value": usd_value,
                    "token_symbol": token_symbol,
                    "token_quantity": token_quantity,
                    "token_price": (
                        event.received_token_price
                        if event.action
                        in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]
                        else event.spent_token_price
                    ),
                    "threshold": self.size_threshold,
                },
            )

        return None
