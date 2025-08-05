# Strategy-Based Transaction Analysis System

This document describes the new strategy-based transaction analysis system that replaces the previous router-based approach.

## Overview

The new system uses a **Strategy Pattern** to analyze blockchain transactions and categorize them based on various criteria. Each strategy evaluates a transaction and returns a `StrategyResult` if the transaction matches the strategy's criteria.

## Key Components

### 1. Strategy Interface

All strategies implement the `TransactionStrategy` abstract base class:

```python
class TransactionStrategy(ABC):
    @property
    def strategy_type(self) -> Strategy: ...

    @property
    def name(self) -> str: ...

    async def evaluate(self, event: UnifiedTransactionEvent) -> Optional[StrategyResult]: ...
```

### 2. Strategy Registry

The `StrategyRegistry` manages all available strategies and provides a centralized way to create and access them:

```python
# Register a strategy class
@register_strategy
class MyStrategy(TransactionStrategy):
    pass

# Create strategy instances
strategy = await strategy_registry.create_strategy("MyStrategy", param1=value1)

# Get all strategies
all_strategies = strategy_registry.get_all_strategies()
```

### 3. Strategy Results

Each strategy returns a `StrategyResult` containing:

- `strategy_name`: The name of the strategy instance
- `strategy_type`: The strategy category (enum)
- `confidence`: Confidence score (0.0 to 1.0)
- `explanation`: Human-readable explanation
- `metadata`: Additional data (optional)

### 4. Database Storage

The system uses a normalized database design with two tables:

#### Strategies Table

```sql
CREATE TABLE strategies (
    id BIGINT PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    strategy_type VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    parameters VARCHAR, -- JSON string of strategy parameters
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at BIGINT NOT NULL
);
```

#### Transaction Strategies Join Table

```sql
CREATE TABLE transaction_strategies (
    id BIGINT PRIMARY KEY,
    transaction_id BIGINT REFERENCES transactions(id) ON DELETE CASCADE,
    strategy_id BIGINT REFERENCES strategies(id) ON DELETE CASCADE,
    confidence FLOAT NOT NULL,
    explanation VARCHAR NOT NULL,
    metadata VARCHAR, -- JSON string
    created_at BIGINT NOT NULL
);
```

This design allows:

- **One-to-many relationship**: A transaction can be associated with multiple strategies
- **Strategy reuse**: Multiple strategy instances can share the same strategy type
- **Parameter storage**: Strategy parameters are stored in the database
- **Active/inactive strategies**: Strategies can be enabled/disabled without deletion

## Available Strategies

### Size-Based Strategies

- **LargeTransactionStrategy**: Identifies transactions above a size threshold
- **WhaleActivityStrategy**: Identifies whale-level transactions

### Volume-Based Strategies

- **HighVolumeStrategy**: Identifies high volume transactions
- **VolumeSpikeStrategy**: Identifies volume spikes relative to daily average

### Wallet-Based Strategies

- **BatchedWalletStrategy**: Identifies coordinated wallet activity

### ML-Based Strategies

- **XGBoostHyperliquidStrategy**: ML model for Hyperliquid transactions
- **XGBoostSolanaStrategy**: ML model for Solana transactions

## Usage Examples

### Creating a Pipeline

```python
from app.services.pipeline.core import CoreTransactionPipeline
from app.services.routers.strategy_registry import strategy_registry

# Create pipeline with all registered strategies
pipeline = await CoreTransactionPipeline.create_with_all_strategies(
    db_writer=transactions_repo,
    alert_router=telegram_alert_router
)

# Or create pipeline with specific strategies
pipeline = await CoreTransactionPipeline.create_with_registered_strategies(
    db_writer=transactions_repo,
    strategy_names=["LargeTransactionStrategy", "WhaleActivityStrategy"],
    alert_router=telegram_alert_router
)
```

### Processing Transactions

```python
# Process a transaction event
await pipeline.handle_event(unified_transaction_event)
```

### Querying Strategy Results

```python
# Get all strategies for a transaction
strategies = await transactions_repo.get_transaction_strategies(transaction_id)

# Get strategy statistics
stats = await transactions_repo.get_strategy_statistics(
    strategy_type=Strategy.LARGE_TRANSACTION,
    start_timestamp=1640995200000,
    end_timestamp=1641081600000
)
```

## Creating Custom Strategies

To create a new strategy:

1. **Define the strategy class**:

```python
from app.services.routers.base import TransactionStrategy, StrategyResult
from app.services.routers.strategy_registry import register_strategy
from app.models.domain.transactions import Strategy

@register_strategy
class MyCustomStrategy(TransactionStrategy):
    def __init__(self, threshold: float = 1000):
        self.threshold = threshold

    @property
    def strategy_type(self) -> Strategy:
        return Strategy.CUSTOM_STRATEGY  # Add to enum first

    @property
    def name(self) -> str:
        return f"My Custom Strategy (threshold: {self.threshold})"

    async def evaluate(self, event: UnifiedTransactionEvent) -> Optional[StrategyResult]:
        # Your evaluation logic here
        if some_condition:
            return StrategyResult(
                strategy_name=self.name,
                strategy_type=self.strategy_type,
                confidence=0.8,
                explanation="Transaction matches custom criteria",
                metadata={"custom_field": "value"}
            )
        return None
```

2. **Add the strategy type to the enum** (if new):

```python
class Strategy(Enum):
    # ... existing strategies ...
    CUSTOM_STRATEGY = "custom_strategy"
```

3. **Import the strategy** in `app/services/routers/__init__.py`

The strategy will automatically be:

- Registered in the strategy registry
- Created in the database when first used
- Available for transaction analysis

## Database Queries

### Strategy Performance Analysis

```sql
-- Which strategies are most profitable?
SELECT
    s.strategy_type,
    s.name as strategy_name,
    COUNT(*) as total_matches,
    AVG(ts.confidence) as avg_confidence,
    COUNT(DISTINCT ts.transaction_id) as unique_transactions
FROM transaction_strategies ts
JOIN strategies s ON ts.strategy_id = s.id
WHERE s.is_active = true
GROUP BY s.strategy_type, s.name
ORDER BY total_matches DESC;
```

### Time-Based Analysis

```sql
-- Strategy performance over time
SELECT
    DATE(FROM_UNIXTIME(t.timestamp / 1000)) as date,
    s.strategy_type,
    s.name as strategy_name,
    COUNT(*) as matches
FROM transaction_strategies ts
JOIN strategies s ON ts.strategy_id = s.id
JOIN transactions t ON ts.transaction_id = t.id
WHERE t.timestamp >= :start_timestamp
  AND s.is_active = true
GROUP BY date, s.strategy_type, s.name
ORDER BY date DESC;
```

### Strategy Parameter Analysis

```sql
-- Analyze strategy performance by parameters
SELECT
    s.name,
    s.parameters,
    COUNT(*) as matches,
    AVG(ts.confidence) as avg_confidence
FROM transaction_strategies ts
JOIN strategies s ON ts.strategy_id = s.id
WHERE s.is_active = true
GROUP BY s.name, s.parameters
ORDER BY matches DESC;
```

## Migration from Old System

The old router-based system has been replaced. Key changes:

1. **ModelRouter** → **TransactionStrategy** (ML strategies)
2. **HeuristicRouter** → **TransactionStrategy** (heuristic strategies)
3. **AlertResult** → **StrategyResult**
4. **should_alert()** → **evaluate()**

The new system provides:

- Better categorization of transactions
- Persistent storage of strategy results
- Analytics capabilities
- More flexible strategy management
- Cleaner separation of concerns
- Normalized database design

## Benefits

1. **Analytics**: Query which strategies are most profitable
2. **Flexibility**: Easy to add new strategies
3. **Persistence**: Strategy results are stored for analysis
4. **Confidence Scoring**: Each strategy provides a confidence level
5. **Metadata**: Rich data for each strategy match
6. **Registry Pattern**: Centralized strategy management
7. **Database Normalization**: Clean, efficient database design
8. **Strategy Management**: Enable/disable strategies without code changes
9. **Parameter Storage**: Strategy parameters stored in database
10. **Scalability**: Efficient queries with proper indexing
