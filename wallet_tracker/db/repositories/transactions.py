"""Simple transaction repository using asyncpg directly."""

import asyncpg
from typing import Optional, Dict, Any
import json
from pydantic import validator

from wallet_tracker.models.common import IDModelMixin
from wallet_tracker.models.domain.rwmodel import RWModel
from wallet_tracker.models.domain.unified_transaction_event import UnifiedTransactionEvent, SUPPORTED_ACTIONS


# Database models for transactions - collocated with repository
class Transaction(RWModel):
    """Transaction model matching UnifiedTransactionEvent structure."""

    action: str
    chain: str
    wallet_address: str
    txn_hash: str
    timestamp: int
    received_token_symbol: str
    received_token_quantity: float
    received_token_price: float
    spent_token_symbol: str
    spent_token_quantity: float
    spent_token_price: float
    transaction_value_usd: float
    # Optional fields
    received_token_id: Optional[str] = None
    spent_token_id: Optional[str] = None
    liquidation: Optional[str] = None  # JSON string
    closed_pnl: Optional[str] = None

    @validator("action")
    def validate_action(cls, v):
        allowed_actions = [action.value for action in SUPPORTED_ACTIONS]
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {allowed_actions}")
        return v


class TransactionStrategy(RWModel):
    """Model for storing strategy evaluation results."""

    transaction_id: int
    strategy_id: int
    explanation: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None

    @validator("metadata", pre=True)
    def validate_metadata(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class TransactionInDB(IDModelMixin, Transaction):
    pass


class TransactionStrategyInDB(IDModelMixin, TransactionStrategy):
    pass


class TransactionsRepository:
    """Simple repository for transactions using asyncpg directly."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_from_unified_event(
        self, event: UnifiedTransactionEvent
    ) -> TransactionInDB:
        """Create a transaction from a UnifiedTransactionEvent."""
        async with self.pool.acquire() as conn:
            # Serialize liquidation if present
            liquidation_json = None
            if event.liquidation:
                liquidation_json = json.dumps(
                    {
                        "liquidatedUser": event.liquidation.liquidatedUser,
                        "markPx": event.liquidation.markPx,
                        "method": event.liquidation.method,
                    }
                )

            row = await conn.fetchrow(
                """
                INSERT INTO transactions (
                    wallet_address,
                    chain,
                    txn_hash,
                    action,
                    timestamp,
                    received_token_symbol,
                    received_token_quantity,
                    received_token_price,
                    received_token_id,
                    spent_token_symbol,
                    spent_token_quantity,
                    spent_token_price,
                    spent_token_id,
                    transaction_value_usd,
                    liquidation,
                    closed_pnl
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                RETURNING *
                """,
                event.wallet_address,
                event.chain,
                event.txn_hash,
                event.action.value,
                event.timestamp,
                event.received_token_symbol,
                event.received_token_quantity,
                event.received_token_price,
                event.received_token_id,
                event.spent_token_symbol,
                event.spent_token_quantity,
                event.spent_token_price,
                event.spent_token_id,
                event.transaction_value_usd,
                liquidation_json,
                event.closed_pnl,
            )

            return TransactionInDB(**dict(row))

    async def transaction_exists(self, txn_hash: str) -> bool:
        """Check if a transaction already exists."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT 1 FROM transactions WHERE txn_hash = $1 LIMIT 1",
                txn_hash,
            )
            return result is not None
