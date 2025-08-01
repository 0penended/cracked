from typing import List
from app.db.repositories.transactions import TransactionsRepository
from app.models.domain.blockchain import UnifiedTransactionEvent
from app.services.routers.base import ModelRouter, HeuristicRouter, AlertRouter, AlertResult


class CoreTransactionPipeline:
    """Core pipeline that processes blockchain events through ML models, heuristics, and alerts."""
    
    def __init__(
        self, 
        db_writer: TransactionsRepository, 
        model_routers: List[ModelRouter], 
        heuristic_routers: List[HeuristicRouter], 
        alert_router: AlertRouter
    ):
        self.db_writer = db_writer
        self.model_routers = model_routers
        self.heuristic_routers = heuristic_routers
        self.alert_router = alert_router

    async def handle_event(self, event: UnifiedTransactionEvent):
        """Process a unified transaction event through the entire pipeline."""
        # Step 1: Write to database
        print("!!!event!!!", event)
        # await self.db_writer.insert(event)

        # # Step 2: Evaluate with ML models and heuristics
        # triggered = False
        # results = []

        # # Apply all ML models
        # for model_router in self.model_routers:
        #     result = await model_router.should_alert(event)
        #     if result.triggered:
        #         triggered = True
        #         results.append(result)

        # # Apply all heuristics
        # for heuristic_router in self.heuristic_routers:
        #     result = await heuristic_router.should_alert(event)
        #     if result.triggered:
        #         triggered = True
        #         results.append(result)

        # # Step 3: Send alert if any triggers were activated
        # if triggered:
        #     await self.alert_router.send(event, results) 