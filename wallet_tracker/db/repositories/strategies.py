"""Simple strategies repository using asyncpg directly."""

import asyncpg
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from wallet_tracker.models.common import IDModelMixin
from wallet_tracker.models.domain.rwmodel import RWModel
from wallet_tracker.db.repositories.transactions import TransactionStrategyInDB


# Database models for strategies - collocated with repository
class Strategy(Enum):
    """Transaction strategy categories that can be identified by various strategies."""

    # Size-based strategies
    LARGE_TRANSACTION = "large_transaction"
    # Volume-based strategies
    HIGH_VOLUME = "high_volume"
    # Wallet-based strategies
    BATCHED_WALLET = "batched_wallet"


@dataclass
class StrategyResult:
    """Result from strategy evaluation."""

    strategy_id: int  # Database ID of the strategy
    type: Strategy  # The strategy category
    explanation: str
    metadata: Optional[dict] = None


class StrategyDefinition(RWModel):
    """Model for strategy definitions in the database."""

    type: Strategy
    description: str
    parameters: str
    is_active: bool = True
    created_at: Optional[int] = None


class StrategyDefinitionInDB(IDModelMixin, StrategyDefinition):
    pass


class StrategiesRepository:
    """Simple repository for strategies using asyncpg directly."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_strategy(
        self,
        strategy_type: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_at: Optional[int] = None,
    ) -> StrategyDefinitionInDB:
        """Create a new strategy definition."""
        if created_at is None:
            created_at = int(datetime.now().timestamp() * 1000)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO strategies (
                    strategy_type,
                    description,
                    parameters,
                    is_active,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                strategy_type,
                description,
                json.dumps(parameters) if parameters else None,
                is_active,
                created_at,
            )

            return StrategyDefinitionInDB(
                id_=row["id"],
                type=Strategy(row["strategy_type"]),
                description=row["description"],
                parameters=row.get("parameters"),
                is_active=row["is_active"],
                created_at=row["created_at"],
            )

    async def get_strategy_by_id(
        self, strategy_id: int
    ) -> Optional[StrategyDefinitionInDB]:
        """Get a strategy by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM strategies WHERE id = $1",
                strategy_id,
            )
            if not row:
                return None

            return StrategyDefinitionInDB(
                id_=row["id"],
                type=Strategy(row["strategy_type"]),
                description=row["description"],
                parameters=row.get("parameters"),
                is_active=row["is_active"],
                created_at=row["created_at"],
            )

    async def save_strategy_results(
        self, transaction_id: int, strategy_results: List[StrategyResult]
    ) -> List[TransactionStrategyInDB]:
        """Save strategy evaluation results."""
        if not strategy_results:
            return []

        created_at = int(time.time() * 1000)
        saved_results = []

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for result in strategy_results:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO transaction_strategies (
                            transaction_id,
                            strategy_id,
                            explanation,
                            metadata,
                            created_at
                        ) VALUES ($1, $2, $3, $4, $5)
                        RETURNING *
                        """,
                        transaction_id,
                        result.strategy_id,
                        result.explanation,
                        json.dumps(result.metadata) if result.metadata else None,
                        created_at,
                    )

                    saved_results.append(TransactionStrategyInDB(**dict(row)))

        return saved_results
