from app.services.routers.base import HeuristicRouter, AlertResult
from app.models.domain.blockchain import UnifiedTransactionEvent


class SizeRouter(HeuristicRouter):
    """Router that triggers on unusual transaction sizes."""

    def __init__(self, size_threshold: float = 100):
        self.size_threshold = size_threshold

    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        # Use received token quantity as the size metric
        if event.recieved_token_quantity > self.size_threshold:
            return AlertResult(
                triggered=True,
                score=0.6,
                explanation=f"Unusual transaction size: {event.recieved_token_quantity}",
            )
        return AlertResult(triggered=False, score=0.0) 