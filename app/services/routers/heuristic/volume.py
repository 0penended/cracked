from app.services.routers.base import HeuristicRouter, AlertResult
from app.models.domain.blockchain import UnifiedTransactionEvent


class VolumeRouter(HeuristicRouter):
    """Router that triggers on high volume transactions."""

    def __init__(self, threshold: float = 1000000):
        self.threshold = threshold

    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        if event.action == "BUY" and event.recieved_token_volume_h24 > self.threshold:
            return AlertResult(
                triggered=True,
                score=1,
                explanation=f"High volume transaction: {event.recieved_token_volume_h24}",
            )
        return AlertResult(triggered=False, score=0.0) 