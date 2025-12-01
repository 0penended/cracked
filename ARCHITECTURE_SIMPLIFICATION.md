# Architecture Simplification Proposal

## Current Architecture Issues

After reviewing the codebase, here are the main complexity issues:

### 1. **Too Many Abstraction Layers**

- `ChainListener` (ABC) → `TransactionFetcher` (separate class) → `ActivityLimiter` (separate class) → `Pipeline` → `TransactionStrategy` (ABC) → `AlertTrigger` (ABC) → `AlertRouter` (ABC)
- **7 layers** for a simple flow: receive → parse → filter → process → alert

### 2. **Over-Engineered Strategy Pattern**

- `TransactionStrategy` ABC
- `StrategyFactory` with database registration
- `StrategyRegistry` (mentioned in docs but may not be used)
- `HyperliquidStrategies` / `SolanaStrategies` factory classes
- Strategy parameter dataclasses
- Database strategy persistence

### 3. **Unnecessary Separation of Concerns**

- `TransactionFetcher` is separate from `Listener` but they're tightly coupled
- `ActivityLimiter` is separate but could be part of pipeline filtering
- `AlertTrigger` is an ABC but could be a simple function

### 4. **Complex Initialization**

- `blockchain_monitor_service.py` has 100+ lines just to wire everything together
- Multiple factory methods and strategy creation patterns

## Simplified Architecture

### Core Principle: **Keep It Simple**

The goal is: Track wallets → Parse transactions → Evaluate → Alert

### Proposed Structure

```
┌─────────────────────────────────────────────────────────┐
│              ChainListener (per chain)                   │
│  - Handles websocket/connection                          │
│  - Parses raw data to UnifiedTransactionEvent            │
│  - Filters spam (activity limiting)                      │
│  - Calls TransactionProcessor                            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         TransactionProcessor (single class)              │
│  - Saves to DB                                           │
│  - Runs evaluation functions (strategies)               │
│  - Decides if should alert (simple function)            │
│  - Sends alert if needed                                 │
└─────────────────────────────────────────────────────────┘
```

### Key Simplifications

#### 1. **Merge TransactionFetcher into Listener**

**Before:**

```python
listener = HyperliquidListener(
    pipeline=pipeline,
    transaction_fetcher=HyperliquidTransactionFetcher(...),
    activity_limiter=WalletActivityLimiter(...)
)
```

**After:**

```python
listener = HyperliquidListener(
    processor=processor,
    coinmarketcap_client=client,  # dependencies injected
    activity_window=60,
    max_tx_per_window=15
)
# Listener handles its own parsing internally
```

**Benefits:**

- One less class to manage
- Listener knows how to parse its own chain's data
- Fewer dependencies to wire up

#### 2. **Simplify Strategy Pattern → Simple Functions**

**Before:**

```python
class TransactionStrategy(ABC):
    @property
    @abstractmethod
    def type(self) -> Strategy: ...

    @abstractmethod
    async def evaluate(...) -> Optional[StrategyResult]: ...

# Plus StrategyFactory, parameter classes, DB registration...
```

**After:**

```python
# Simple callable type
StrategyEvaluator = Callable[
    [UnifiedTransactionEvent, TransactionRepository],
    Awaitable[Optional[StrategyResult]]
]

# Example strategy (just a function)
async def large_transaction_strategy(
    event: UnifiedTransactionEvent,
    repo: TransactionRepository
) -> Optional[StrategyResult]:
    value = get_transaction_value(event)
    if value > 100000:
        return StrategyResult(
            type=Strategy.LARGE_TRANSACTION,
            confidence=1.0,
            explanation=f"Transaction value ${value:,.2f} exceeds threshold"
        )
    return None

# Or if you need state, use a simple class:
class BatchedWalletStrategy:
    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self._recent_txs = defaultdict(list)

    async def __call__(
        self, event: UnifiedTransactionEvent, repo: TransactionRepository
    ) -> Optional[StrategyResult]:
        # Implementation
        ...
```

**Benefits:**

- No ABC overhead
- No factory pattern
- No database registration complexity
- Strategies are just functions or simple classes
- Easy to test and understand

#### 3. **Merge ActivityLimiter into Pipeline/Processor**

**Before:**

```python
if activity_limiter.record_and_check(wallet, qualifying=txn_value < 1000):
    return
await pipeline.handle_event(event)
```

**After:**

```python
# Activity limiting is part of processor
class TransactionProcessor:
    def __init__(self, ..., activity_window=60, max_tx_per_window=15):
        self.activity_limiter = WalletActivityLimiter(...)

    async def process(self, event: UnifiedTransactionEvent):
        # Check activity limit
        if self.activity_limiter.is_blacklisted(event.wallet_address):
            return

        # Continue processing...
```

**Benefits:**

- One less thing to pass around
- Activity limiting is part of processing logic

#### 4. **Simplify AlertTrigger → Function**

**Before:**

```python
class AlertTrigger(ABC):
    @abstractmethod
    def should_alert(...) -> bool: ...

class AlertTriggerStrategyMatchQuantity(AlertTrigger):
    def should_alert(self, results: List[StrategyResult]) -> bool:
        return len(results) >= self.quantity
```

**After:**

```python
# Just a function
def should_alert(
    strategy_results: List[StrategyResult],
    min_matches: int = 2
) -> bool:
    return len(strategy_results) >= min_matches

# Or if you need more complex logic:
AlertDecider = Callable[[List[StrategyResult]], bool]
```

**Benefits:**

- No ABC overhead
- Simple to understand and test
- Easy to customize per chain

#### 5. **Consolidate TransactionProcessor**

**Before:**

- `CoreTransactionPipeline` handles processing
- `AlertRouter` handles alerts
- `AlertTrigger` decides when to alert
- `StrategiesRepository` saves strategy results
- `TransactionsRepository` saves transactions

**After:**

```python
class TransactionProcessor:
    """Single class that handles all transaction processing."""

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        strategies: List[StrategyEvaluator],
        alert_sender: AlertSender,  # Simple interface
        should_alert: AlertDecider,  # Function
        activity_limiter: WalletActivityLimiter,
    ):
        ...

    async def process(self, event: UnifiedTransactionEvent):
        # 1. Filter by activity
        if self.activity_limiter.is_blacklisted(event.wallet_address):
            return

        # 2. Filter by value
        if get_transaction_value(event) < 1000:
            return

        # 3. Save transaction
        tx = await self.transaction_repo.create_from_unified_event(event)

        # 4. Evaluate strategies
        results = []
        for strategy in self.strategies:
            result = await strategy(event, self.transaction_repo)
            if result:
                results.append(result)

        # 5. Save strategy results
        if results:
            await self.transaction_repo.save_strategy_results(tx.id_, results)

        # 6. Check if should alert
        if results and self.should_alert(results):
            await self.alert_sender.send(event, results)
```

**Benefits:**

- Single class, single responsibility: process transactions
- Clear flow: filter → save → evaluate → alert
- Easy to understand and modify

## Simplified Code Structure

### New File Structure

```
app/services/
├── listeners/
│   ├── base.py              # Simple ChainListener ABC (keep minimal)
│   ├── hyperliquid.py       # Handles websocket + parsing internally
│   └── solana.py            # Handles websocket + parsing internally
│
├── processor.py             # Single TransactionProcessor class
│
├── strategies/
│   ├── __init__.py          # Export strategy functions
│   ├── size.py              # large_transaction_strategy()
│   ├── volume.py            # high_volume_strategy()
│   └── batched_wallet.py    # BatchedWalletStrategy class
│
├── alerts.py                 # Simple alert sending (TelegramAlertSender)
│
└── blockchain_monitor_service.py  # Much simpler setup
```

### Simplified `blockchain_monitor_service.py`

**Before:** ~200 lines with complex wiring

**After:** ~80 lines

```python
class BlockchainMonitorService:
    async def start(self):
        # Setup
        db_pool = await asyncpg.create_pool(...)
        transaction_repo = TransactionRepository(db_pool)

        # Create clients
        coinmarketcap = CoinMarketCapClient(...)
        telegram = TelegramClient(...)

        # Define strategies (just functions/classes)
        hyperliquid_strategies = [
            large_transaction_strategy,
            BatchedWalletStrategy(threshold=3),
        ]

        solana_strategies = [
            high_volume_strategy,
            large_transaction_strategy,
            BatchedWalletStrategy(threshold=5),
        ]

        # Create processors
        hl_processor = TransactionProcessor(
            transaction_repo=transaction_repo,
            strategies=hyperliquid_strategies,
            alert_sender=TelegramAlertSender(telegram, chat_id, "Hyperliquid"),
            should_alert=lambda results: len(results) >= 2,
            activity_limiter=WalletActivityLimiter(...),
        )

        sol_processor = TransactionProcessor(
            transaction_repo=transaction_repo,
            strategies=solana_strategies,
            alert_sender=TelegramAlertSender(telegram, chat_id, "Solana"),
            should_alert=lambda results: len(results) >= 2,
            activity_limiter=WalletActivityLimiter(...),
        )

        # Create listeners (they handle their own parsing)
        self.hyperliquid_listener = HyperliquidListener(
            processor=hl_processor,
            coinmarketcap_client=coinmarketcap,
        )

        self.solana_listener = SolanaListener(
            processor=sol_processor,
            dex_screener_client=DexScreenerClient(),
            rpc_url=settings.solana_rpc_url,
        )

        # Start
        self.hyperliquid_listener.subscribe_wallets(get_hyperliquid_addresses())
        self.solana_listener.subscribe_wallets(get_solana_addresses())

        asyncio.create_task(self._run())
```

## Migration Strategy

### Phase 1: Simplify Strategies (Low Risk)

1. Convert strategies to functions/simple classes
2. Remove StrategyFactory, StrategyRegistry
3. Keep database saving but simplify

### Phase 2: Merge Fetchers into Listeners (Medium Risk)

1. Move parsing logic into listeners
2. Remove TransactionFetcher classes
3. Update listeners to call processor directly

### Phase 3: Consolidate Processor (Medium Risk)

1. Merge ActivityLimiter into processor
2. Simplify AlertTrigger to function
3. Consolidate all processing logic

### Phase 4: Clean Up (Low Risk)

1. Remove unused ABCs
2. Simplify imports
3. Update documentation

## Benefits Summary

1. **Reduced Complexity**: 7 layers → 2 layers
2. **Easier to Understand**: Clear flow, fewer abstractions
3. **Easier to Test**: Functions are easier to test than ABCs
4. **Easier to Extend**: Add new strategy = add new function
5. **Less Code**: ~40% reduction in boilerplate
6. **Faster Development**: Less time wiring things together

## What to Keep

- `UnifiedTransactionEvent` model (good abstraction)
- Database repositories (good separation)
- Client classes (CoinMarketCap, DexScreener, Telegram)
- Activity limiting logic (just move it into processor)
- Strategy results and database storage (useful for analytics)

## What to Remove/Simplify

- `TransactionStrategy` ABC → functions
- `StrategyFactory` → direct instantiation
- `StrategyRegistry` → not needed
- `TransactionFetcher` classes → merge into listeners
- `AlertTrigger` ABC → function
- `AlertRouter` ABC → simple `AlertSender` class
- Complex strategy parameter classes → simple dict or kwargs

## Example: Before vs After

### Before (Complex)

```python
# 1. Create factory
factory = StrategyFactory(db_repository)

# 2. Create strategies with params
strategies = [
    await factory.create_large_transaction(
        LargeTransactionParams(size_threshold=100000)
    ),
    await factory.create_batched_wallet(
        BatchedWalletParams(batch_threshold=3, time_window=1800)
    ),
]

# 3. Create alert trigger
alert_trigger = AlertTriggerStrategyMatchQuantity(quantity=2)

# 4. Create pipeline
pipeline = CoreTransactionPipeline(
    strategies=strategies,
    alert_router=TelegramAlertRouter(...),
    alert_trigger=alert_trigger,
    ...
)

# 5. Create fetcher
fetcher = HyperliquidTransactionFetcher(...)

# 6. Create limiter
limiter = WalletActivityLimiter(...)

# 7. Create listener
listener = HyperliquidListener(
    pipeline=pipeline,
    transaction_fetcher=fetcher,
    activity_limiter=limiter
)
```

### After (Simple)

```python
# 1. Define strategies (just functions/classes)
strategies = [
    lambda e, r: large_transaction_strategy(e, r, threshold=100000),
    BatchedWalletStrategy(threshold=3, time_window=1800),
]

# 2. Create processor
processor = TransactionProcessor(
    transaction_repo=repo,
    strategies=strategies,
    alert_sender=TelegramAlertSender(...),
    should_alert=lambda results: len(results) >= 2,
    activity_limiter=WalletActivityLimiter(...),
)

# 3. Create listener (handles its own parsing)
listener = HyperliquidListener(
    processor=processor,
    coinmarketcap_client=client,
)
```

**Reduction: 7 steps → 3 steps, ~70% less code**
