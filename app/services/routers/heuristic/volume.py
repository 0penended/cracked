from app.services.routers.base import TransactionStrategy, StrategyResult
from app.models.domain.blockchain import UnifiedTransactionEvent, Action
from app.models.domain.strategy import Strategy


class HighVolumeStrategy(TransactionStrategy):
    """Strategy that identifies high volume transactions."""

    def __init__(self, threshold: float = 1000000, strategy_id: int = None):
        super().__init__(strategy_id=strategy_id)
        self.threshold = threshold

    @property
    def type(self) -> Strategy:
        return Strategy.HIGH_VOLUME

    @property
    def description(self) -> str:
        return f"High Volume (${self.threshold:,.0f}+)"

    async def evaluate(self, event: UnifiedTransactionEvent) -> StrategyResult:
        # Determine which volume to check based on the action
        volume_to_check = self._get_volume_for_action(event)

        if volume_to_check > self.threshold:
            action_name = event.action.value
            confidence = min(1.0, (volume_to_check / self.threshold) * 0.4)

            return StrategyResult(
                strategy_id=self.strategy_id,
                type=self.type,
                confidence=confidence,
                explanation=f"High volume {action_name} transaction: {volume_to_check:,.0f}",
                metadata={
                    "volume": volume_to_check,
                    "action": action_name,
                    "threshold": self.threshold,
                    "usd_value": volume_to_check,  # For volume strategies, volume is the USD value
                    "token_symbol": (
                        event.received_token_symbol
                        if event.action
                        in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]
                        else event.spent_token_symbol
                    ),
                    "token_quantity": (
                        event.received_token_quantity
                        if event.action
                        in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]
                        else event.spent_token_amount
                    ),
                    "token_price": (
                        event.received_token_price
                        if event.action
                        in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]
                        else event.spent_token_price
                    ),
                },
            )

        return None

    def _get_volume_for_action(self, event: UnifiedTransactionEvent) -> float:
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
            if (
                event.received_token_symbol == "USD"
                or event.received_token_symbol == "USDC"
            ):
                return spent_volume
            elif (
                event.spent_token_symbol == "USD" or event.spent_token_symbol == "USDC"
            ):
                return received_volume
            else:
                # Both are non-USD tokens, use the higher volume
                return max(received_volume, spent_volume)

        # Default fallback
        else:
            return max(event.received_token_volume_h24, event.spent_token_volume_h24)


# class VolumeSpikeStrategy(TransactionStrategy):
#     """Strategy that identifies volume spikes relative to normal trading volume."""

#     def __init__(self, spike_multiplier: float = 5.0, strategy_id: int = None):
#         super().__init__(strategy_id=strategy_id)
#         self.spike_multiplier = spike_multiplier

#     @property
#     def type(self) -> Strategy:
#         return Strategy.VOLUME_SPIKE

#     @property
#     def description(self) -> str:
#         return f"Volume Spike ({self.spike_multiplier}x+)"

#     async def evaluate(self, event: UnifiedTransactionEvent) -> StrategyResult:
#         # Get the transaction volume
#         transaction_volume = self._get_volume_for_action(event)

#         # Get the 24h volume for comparison
#         if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
#             daily_volume = event.received_token_volume_h24
#             token_symbol = event.recieved_token_symbol
#         elif event.action in [Action.SELL, Action.OPEN_SHORT, Action.CLOSE_LONG]:
#             daily_volume = event.spent_token_volume_h24
#             token_symbol = event.spent_token_symbol
#         else:
#             daily_volume = max(
#                 event.received_token_volume_h24, event.spent_token_volume_h24
#             )
#             token_symbol = event.received_token_symbol or event.spent_token_symbol

#         if daily_volume > 0 and transaction_volume > (
#             daily_volume * self.spike_multiplier
#         ):
#             confidence = min(
#                 1.0, (transaction_volume / (daily_volume * self.spike_multiplier)) * 0.3
#             )

#             return StrategyResult(
#                 strategy_id=self.strategy_id,
#                 type=self.type,
#                 confidence=confidence,
#                 explanation=f"Volume spike: {transaction_volume:,.0f} vs daily avg {daily_volume:,.0f} ({token_symbol})",
#                 metadata={
#                     "transaction_volume": transaction_volume,
#                     "daily_volume": daily_volume,
#                     "spike_ratio": transaction_volume / daily_volume,
#                     "token_symbol": token_symbol,
#                     "multiplier": self.spike_multiplier,
#                 },
#             )

#         return None

#     def _get_volume_for_action(self, event: UnifiedTransactionEvent) -> float:
#         """Get the appropriate volume to check based on the transaction action."""
#         # Same logic as HighVolumeStrategy
#         if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
#             return event.received_token_volume_h24
#         elif event.action in [Action.SELL, Action.OPEN_SHORT, Action.CLOSE_LONG]:
#             return event.spent_token_volume_h24
#         elif event.action == Action.SWAP:
#             received_volume = event.received_token_volume_h24
#             spent_volume = event.spent_token_volume_h24
#             if event.recieved_token_symbol in ["USD", "USDC"]:
#                 return spent_volume
#             elif event.spent_token_symbol in ["USD", "USDC"]:
#                 return received_volume
#             else:
#                 return max(received_volume, spent_volume)
#         else:
#             return max(event.received_token_volume_h24, event.spent_token_volume_h24)
