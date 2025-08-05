from typing import Optional, Dict, Any
from enum import Enum
import json
import time

from pydantic import validator

from app.models.common import IDModelMixin
from app.models.domain.rwmodel import RWModel


class Strategy(Enum):
    """Transaction strategy categories that can be identified by various strategies."""

    # Size-based strategies
    LARGE_TRANSACTION = "large_transaction"

    # Volume-based strategies
    HIGH_VOLUME = "high_volume"

    # Wallet-based strategies
    BATCHED_WALLET = "batched_wallet"

    # ML-based strategies
    XG_BOOST_HL = "xg_boost_hl"
    XG_BOOST_SOL = "xg_boost_sol"


class StrategyDefinition(RWModel):
    """Model for strategy definitions in the database."""

    type: Strategy
    description: str
    parameters: str
    is_active: bool = True
    created_at: Optional[int] = None

    # For now, keep parameters as string - no JSON parsing
    # @validator("parameters", pre=True)
    # def validate_parameters(cls, v):
    #     if isinstance(v, str):
    #         return json.loads(v)
    #     return v


class StrategyDefinitionInDB(IDModelMixin, StrategyDefinition):
    pass
