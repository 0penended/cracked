from app.services.routers.base import HeuristicRouter, AlertResult
from app.models.domain.blockchain import UnifiedTransactionEvent, Action


class VolumeRouter(HeuristicRouter):
    """Router that triggers on high volume transactions."""

    def __init__(self, threshold: float = 1000000):
        self.threshold = threshold

    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        # Determine which volume to check based on the action
        volume_to_check = self._get_volume_for_action(event)

        if volume_to_check > self.threshold:
            action_name = event.action.value
            return AlertResult(
                triggered=True,
                score=1,
                explanation=f"High volume {action_name} transaction: {volume_to_check:,.0f}",
            )
        return AlertResult(triggered=False, score=0.0)

    def _get_volume_for_action(self, event: UnifiedTransactionEvent) -> float:
        """Get the appropriate volume to check based on the transaction action."""

        # For all actions, we want to check the non-USD token volume
        # USD is typically the collateral, so we check the actual asset volume

        # Actions where we're receiving the asset (not USD)
        if event.action in [Action.BUY, Action.OPEN_LONG, Action.CLOSE_SHORT]:
            # Use received token volume (the asset we're acquiring)
            return event.recieved_token_volume_h24

        # Actions where we're spending the asset (not USD)
        elif event.action in [Action.SELL, Action.OPEN_SHORT, Action.CLOSE_LONG]:
            # Use spent token volume (the asset we're disposing)
            return event.spent_token_volume_h24

        # For SWAP actions, use the higher volume between received and spent
        # (excluding USD if it's one of the tokens)
        elif event.action == Action.SWAP:
            received_volume = event.recieved_token_volume_h24
            spent_volume = event.spent_token_volume_h24

            # If one of the tokens is USD, use the other token's volume
            if (
                event.recieved_token_symbol == "USD"
                or event.recieved_token_symbol == "USDC"
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
            return max(event.recieved_token_volume_h24, event.spent_token_volume_h24)
