import asyncpg
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime


from app.models.domain.strategy import StrategyDefinitionInDB, Strategy
from app.models.domain.transactions import TransactionStrategyInDB
from app.services.routers.base import StrategyResult
from app.db.queries.queries import queries


class StrategiesRepository:
    """Repository for managing strategy definitions and results."""

    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def create_strategy(
        self,
        strategy_type: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_at: Optional[int] = None,
    ) -> StrategyDefinitionInDB:
        """Create a new strategy definition in the database."""
        if created_at is None:
            created_at = int(datetime.now().timestamp() * 1000)

        async with self.connection.transaction():
            strategy_row = await queries.create_strategy(
                self.connection,
                type=strategy_type,
                description=description,
                parameters=json.dumps(parameters) if parameters else None,
                is_active=is_active,
                created_at=created_at,
            )

        # Map database fields to model fields
        record_dict = strategy_row[0]
        return StrategyDefinitionInDB(
            id_=record_dict["id"],
            type=Strategy(record_dict["type"]),
            description=record_dict["description"],
            parameters=record_dict.get("parameters"),  # Keep as string for now
            is_active=record_dict.get("is_active", True),
            created_at=record_dict.get("created_at"),
        )

    async def get_strategy_by_type(
        self, strategy_type: str
    ) -> Optional[StrategyDefinitionInDB]:
        """Get a strategy definition by type (assumes type is unique)."""
        strategy_row = await queries.get_strategy_by_type(
            self.connection, type=strategy_type
        )
        if strategy_row:
            # Map database fields to model fields
            return StrategyDefinitionInDB(
                id_=strategy_row[0]["id"],
                type=Strategy(strategy_row[0]["type"]),
                description=strategy_row[0]["description"],
                parameters=strategy_row[0].get("parameters"),  # Keep as string for now
                is_active=strategy_row[0].get("is_active", True),
                created_at=strategy_row[0].get("created_at"),
            )
        return None

    async def get_all_active_strategies(self) -> List[StrategyDefinitionInDB]:
        """Get all active strategy definitions."""
        strategy_rows = await queries.get_all_active_strategies(self.connection)

        return [
            StrategyDefinitionInDB(
                id_=row["id"],
                type=Strategy(row["type"]),
                description=row["description"],
                parameters=row.get("parameters"),  # Keep as string for now
                is_active=row.get("is_active", True),
                created_at=row.get("created_at"),
            )
            for row in strategy_rows
        ]

    async def save_strategy_results(
        self, transaction_id: int, strategy_results: List[StrategyResult]
    ) -> List[TransactionStrategyInDB]:
        """Save strategy evaluation results for a transaction."""
        saved_strategies = []

        for result in strategy_results:
            # Use the strategy_id directly from the result - no need for database lookup!
            if result.strategy_id is None:
                print(f"Warning: Strategy with type {result.type} has no strategy_id")
                continue

            strategy = TransactionStrategyInDB(
                transaction_id=transaction_id,
                strategy_id=result.strategy_id,
                confidence=result.confidence,
                explanation=result.explanation,
                metadata=result.metadata,
            )

            async with self.connection.transaction():
                strategy_row = await queries.create_transaction_strategy(
                    self.connection,
                    transaction_id=strategy.transaction_id,
                    strategy_id=strategy.strategy_id,
                    confidence=strategy.confidence,
                    explanation=strategy.explanation,
                    metadata=(
                        json.dumps(strategy.metadata) if strategy.metadata else None
                    ),
                    created_at=strategy.created_at or int(time.time() * 1000),
                )

            saved_strategies.append(strategy)

        return saved_strategies

    async def get_transaction_strategies(
        self, transaction_id: int
    ) -> List[TransactionStrategyInDB]:
        """Get all strategy results for a specific transaction."""
        strategy_rows = await queries.get_transaction_strategies(
            self.connection, transaction_id=transaction_id
        )

        return [
            TransactionStrategyInDB(
                id_=row["id"],
                transaction_id=row["transaction_id"],
                strategy_id=row["strategy_id"],
                confidence=row["confidence"],
                explanation=row["explanation"],
                metadata=row.get("metadata"),
                created_at=row.get("created_at"),
            )
            for row in strategy_rows
        ]

    async def get_strategy_statistics(
        self,
        strategy_type: Optional[str] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get statistics about strategy performance."""
        stats_rows = await queries.get_strategy_statistics(
            self.connection,
            type=strategy_type,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )

        return [
            {
                "type": row["type"],
                "strategy_description": row["strategy_description"],
                "total_matches": row["total_matches"],
                "avg_confidence": (
                    float(row["avg_confidence"]) if row["avg_confidence"] else 0.0
                ),
                "min_confidence": (
                    float(row["min_confidence"]) if row["min_confidence"] else 0.0
                ),
                "max_confidence": (
                    float(row["max_confidence"]) if row["max_confidence"] else 0.0
                ),
                "unique_transactions": row["unique_transactions"],
            }
            for row in stats_rows
        ]
