from dataclasses import dataclass
from typing import List, Optional, TypeVar, Type
from app.services.routers.base import TransactionStrategy
from app.services.routers.heuristic.size import (
    LargeTransactionStrategy,
)
from app.services.routers.heuristic.volume import (
    HighVolumeStrategy,
)
from app.services.routers.heuristic.batched_wallet import BatchedWalletStrategy
from app.models.domain.strategy import StrategyDefinitionInDB
from app.db.repositories.strategies import StrategiesRepository


# Parameter classes for each strategy type
@dataclass
class LargeTransactionParams:
    size_threshold: float = 10000


@dataclass
class HighVolumeParams:
    threshold: float = 1000000


# @dataclass
# class VolumeSpikeParams:
#     spike_multiplier: float = 5.0


@dataclass
class BatchedWalletParams:
    batch_threshold: int = 5
    time_window: int = 1800


@dataclass
class XGBoostParams:
    confidence_threshold: float = 0.7


T = TypeVar("T", bound=TransactionStrategy)


class StrategyFactory:
    """Type-safe factory for creating strategy instances with automatic database registration."""

    def __init__(self, db_repository: Optional[StrategiesRepository] = None):
        self.db_repository = db_repository
        self._strategy_cache: dict[str, StrategyDefinitionInDB] = {}

    def set_db_repository(self, db_repository: StrategiesRepository) -> None:
        """Set the database repository for automatic strategy registration."""
        self.db_repository = db_repository

    async def _ensure_strategy_in_database(
        self, strategy_instance: TransactionStrategy, params: dataclass
    ) -> Optional[int]:
        """Ensure a strategy exists in the database and return its ID."""
        if not self.db_repository:
            return None

        # Generate unique identifier based on strategy type and parameters
        param_str = "_".join(f"{k}_{v}" for k, v in sorted(params.__dict__.items()))
        unique_identifier = f"{strategy_instance.type.value}_{param_str}"

        # Check cache first
        if unique_identifier in self._strategy_cache:
            return self._strategy_cache[unique_identifier].id_

        # Check if strategy exists in database
        try:
            strategy_def = await self.db_repository.get_strategy_by_type(
                strategy_instance.type.value
            )
            if strategy_def:
                self._strategy_cache[unique_identifier] = strategy_def
                return strategy_def.id_
        except Exception as e:
            print(f"Warning: Error looking up strategy in database: {e}")
            # Continue to create new strategy

        # Create strategy in database
        try:
            saved_strategy = await self.db_repository.create_strategy(
                strategy_type=strategy_instance.type.value,
                description=strategy_instance.description,
                parameters=params.__dict__,
                is_active=True,
            )
            self._strategy_cache[unique_identifier] = saved_strategy
            return saved_strategy.id_
        except Exception as e:
            print(f"Warning: Error creating strategy in database: {e}")
            return None

    async def _create_strategy_with_db_registration(
        self, strategy_class: Type[T], params: dataclass, **kwargs
    ) -> T:
        """Generic method to create a strategy and register it in the database."""
        # Create strategy instance without ID first
        strategy = strategy_class(**kwargs)

        # Ensure it's registered in the database and get the ID
        strategy_id = None
        if self.db_repository:
            strategy_id = await self._ensure_strategy_in_database(strategy, params)

        # Create a new instance with the strategy ID
        strategy_with_id = strategy_class(strategy_id=strategy_id, **kwargs)

        return strategy_with_id

    async def create_large_transaction(
        self, params: LargeTransactionParams
    ) -> LargeTransactionStrategy:
        """Create a large transaction strategy with explicit parameters."""
        return await self._create_strategy_with_db_registration(
            LargeTransactionStrategy, params, size_threshold=params.size_threshold
        )

    async def create_high_volume(self, params: HighVolumeParams) -> HighVolumeStrategy:
        """Create a high volume strategy with explicit parameters."""
        return await self._create_strategy_with_db_registration(
            HighVolumeStrategy, params, threshold=params.threshold
        )

    async def create_batched_wallet(
        self, params: BatchedWalletParams
    ) -> BatchedWalletStrategy:
        """Create a batched wallet strategy with explicit parameters."""
        return await self._create_strategy_with_db_registration(
            BatchedWalletStrategy,
            params,
            batch_threshold=params.batch_threshold,
            time_window=params.time_window,
        )

    # async def create_xgboost_solana(
    #     self, params: XGBoostParams
    # ) -> XGBoostSolanaStrategy:
    #     """Create an XGBoost Solana strategy with explicit parameters."""
    #     return await self._create_strategy_with_db_registration(
    #         XGBoostSolanaStrategy,
    #         params,
    #         confidence_threshold=params.confidence_threshold,
    #     )


# Predefined strategy configurations for different chains
class HyperliquidStrategies:
    """Predefined strategy configurations for Hyperliquid."""

    @staticmethod
    async def create_all(
        db_repository: StrategiesRepository,
    ) -> List[TransactionStrategy]:
        """Create all Hyperliquid strategies with optimized parameters."""
        factory = StrategyFactory(db_repository)

        return [
            await factory.create_high_volume(HighVolumeParams(threshold=1000000)),
            await factory.create_batched_wallet(
                BatchedWalletParams(batch_threshold=3, time_window=1800)
            ),
            await factory.create_large_transaction(
                LargeTransactionParams(size_threshold=10000)
            ),
        ]


class SolanaStrategies:
    """Predefined strategy configurations for Solana."""

    @staticmethod
    async def create_all(
        db_repository: StrategiesRepository,
    ) -> List[TransactionStrategy]:
        """Create all Solana strategies with optimized parameters."""
        factory = StrategyFactory(db_repository)

        return [
            await factory.create_high_volume(HighVolumeParams(threshold=1000000)),
            await factory.create_batched_wallet(
                BatchedWalletParams(batch_threshold=5, time_window=1800)
            ),
            await factory.create_large_transaction(
                LargeTransactionParams(size_threshold=10000)
            ),
        ]
