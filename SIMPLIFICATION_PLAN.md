# Architecture Simplification - Implementation Plan

## Overview

This document breaks down the simplification work into 3 discrete, manageable sections. Each section can be completed independently and tested before moving to the next.

## Section 1: Simplify to Core Abstractions (Listeners, Processors, Storage)

**Goal:** Reduce the architecture to just 3 core components:
- **Listeners**: Handle websocket connections and parse chain-specific data
- **Processors**: Process transactions (filter, evaluate, alert)
- **Storage**: Database writes (repositories)

**What we'll do:**
1. Create a simple `TransactionProcessor` class that consolidates:
   - Activity limiting (move from separate class)
   - Transaction saving
   - Strategy evaluation
   - Alert decision and sending
2. Simplify strategies to use a Protocol (structural typing) instead of ABC
3. Merge `TransactionFetcher` logic into `Listener` classes
4. Remove `CoreTransactionPipeline`, `AlertTrigger` ABC, `AlertRouter` ABC
5. Simplify `blockchain_monitor_service.py` setup

**Deliverables:**
- New `TransactionProcessor` class
- Simplified `HyperliquidListener` (with parsing built-in)
- Simplified `SolanaListener` (with parsing built-in)
- Updated `blockchain_monitor_service.py`
- Strategy Protocol definition

**Testing:**
- Verify transactions still flow: Listener → Processor → Storage
- Verify alerts still work
- Verify activity limiting still works

---

## Section 2: Simplify Strategy Pattern

**Goal:** Convert strategies from complex ABC + Factory pattern to simple functions/classes with Protocol.

**What we'll do:**
1. Define `StrategyEvaluator` Protocol (structural typing, not ABC)
2. Convert existing strategies to simple functions or classes
3. Remove `StrategyFactory`, `StrategyRegistry`, parameter dataclasses
4. Simplify strategy database storage (keep it but simplify the interface)
5. Update processor to use new strategy pattern

**Deliverables:**
- `StrategyEvaluator` Protocol
- Converted strategy functions/classes in `app/services/strategies/`
- Simplified strategy database interface
- Updated processor to use new strategies

**Testing:**
- Verify all strategies still evaluate correctly
- Verify strategy results still save to database
- Verify alerts trigger based on strategy results

---

## Section 3: Clean Up and Optimize

**Goal:** Remove unused code, simplify imports, update documentation.

**What we'll do:**
1. Remove unused ABCs (`TransactionStrategy`, `AlertTrigger`, `AlertRouter`)
2. Remove unused factory classes
3. Clean up imports across codebase
4. Update documentation files
5. Simplify any remaining complex patterns

**Deliverables:**
- Cleaned codebase (removed unused files)
- Updated documentation
- Simplified imports

**Testing:**
- Full integration test
- Verify nothing broke

---

## Strategy Protocol Design

Since we need uniform calling but want to avoid ABC overhead, we'll use Python's `Protocol`:

```python
from typing import Protocol, Optional
from app.models.domain.blockchain import UnifiedTransactionEvent
from app.db.repositories.transactions import TransactionsRepository
from app.services.routers.base import StrategyResult

class StrategyEvaluator(Protocol):
    """Protocol for strategy evaluation - allows functions or classes."""
    
    async def __call__(
        self,
        event: UnifiedTransactionEvent,
        transaction_repo: TransactionsRepository,
    ) -> Optional[StrategyResult]:
        """Evaluate transaction and return result if strategy matches."""
        ...
```

This allows:
- Functions: `async def my_strategy(event, repo) -> Optional[StrategyResult]: ...`
- Classes: `class MyStrategy: async def __call__(self, event, repo): ...`
- Both can be called uniformly: `await strategy(event, repo)`

---

## Migration Notes

- Each section is independent and can be tested separately
- We'll keep the old code working while building new code
- After each section, we can verify everything still works
- Final cleanup removes old code

