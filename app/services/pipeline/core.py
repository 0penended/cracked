from typing import List
from loguru import logger

from app.models.domain.blockchain import UnifiedTransactionEvent
from app.services.routers.base import TransactionStrategy, AlertRouter, AlertTrigger
from app.db.repositories.transactions import TransactionsRepository
from app.db.repositories.strategies import StrategiesRepository


class CoreTransactionPipeline:
    """Core pipeline for processing blockchain transactions."""

    def __init__(
        self,
        strategies: List[TransactionStrategy],
        alert_router: AlertRouter,
        alert_trigger: AlertTrigger,
        strategies_repository: StrategiesRepository,
        transaction_repository: TransactionsRepository,
    ):
        self.strategies = strategies
        self.alert_router = alert_router
        self.alert_trigger = alert_trigger
        self.strategies_repository = strategies_repository
        self.transaction_repository = transaction_repository

    async def handle_event(self, event: UnifiedTransactionEvent) -> None:
        """Process a blockchain transaction event."""
        try:
            logger.info(f"🔄 Processing transaction: {event.txn_hash}")
            logger.debug(f"Transaction details: {event.action} on {event.chain}")

            logger.info(f"💾 Saving transaction to database: {event.txn_hash}")
            try:
                saved_transaction = (
                    await self.transaction_repository.create_from_unified_event(event)
                )
                logger.info(f"✅ Transaction saved with ID: {saved_transaction.id_}")
            except Exception as e:
                logger.error(f"❌ Error saving transaction {event.txn_hash}: {e}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

            # Evaluate all strategies
            strategy_results = []
            logger.info(f"🔍 Evaluating {len(self.strategies)} strategies")
            for strategy in self.strategies:
                try:
                    logger.info(f"Evaluating strategy: {strategy.description}")
                    result = await strategy.evaluate(event)
                    if result:
                        logger.info(
                            f"✅ Strategy {strategy.description} matched with confidence {result.confidence}"
                        )
                        strategy_results.append(result)
                    else:
                        logger.debug(
                            f"❌ Strategy {strategy.description} did not match"
                        )
                except Exception as e:
                    logger.error(
                        f"Error evaluating strategy {strategy.description}: {e}"
                    )

            # Save strategy results
            if strategy_results:
                logger.info(
                    f"💾 Saving {len(strategy_results)} strategy results: {strategy_results}"
                )
                await self.strategies_repository.save_strategy_results(
                    saved_transaction.id_, strategy_results
                )
                logger.info(f"✅ Strategy results saved")

            # Check if we should send an alert based on the alert trigger
            if strategy_results and self.alert_trigger.should_alert(strategy_results):
                logger.info(f"🚨 Alert trigger conditions met, sending alert")
                await self.alert_router.send(strategy_results)
                logger.info(
                    f"Alert sent for transaction {event.txn_hash} with {len(strategy_results)} strategy matches"
                )
            elif strategy_results:
                logger.info(
                    f"Strategy matches found for transaction {event.txn_hash} ({len(strategy_results)} matches) but alert trigger conditions not met"
                )

            logger.info(
                f"✅ Completed processing transaction {event.txn_hash} with {len(strategy_results)} strategy matches"
            )

        except Exception as e:
            logger.error(f"❌ Error processing transaction {event.txn_hash}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
