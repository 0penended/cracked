# Database Layer Simplification

## Overview

Simplified the database access layer by removing unnecessary abstractions and dependencies. The new approach uses `asyncpg` directly with raw SQL, keeping only Alembic for migrations.

## What Was Removed

### Dependencies Removed
- **`aiosql`** - SQL file loader (replaced with raw SQL strings)
- **`pypika`** - Query builder (replaced with raw SQL strings)

### Code Removed
- `app/db/queries/queries.py` - aiosql query loader
- `app/db/queries/tables.py` - pypika table definitions
- `app/db/queries/sql/` - SQL files directory
- `app/db/repositories/base.py` - BaseRepository class

## What Was Kept

- **`asyncpg`** - Direct PostgreSQL async driver (core dependency)
- **`alembic`** - Migration tool (standard, works well)
- **`sqlalchemy`** - Only used by Alembic for migrations (not for ORM)

## New Structure

### Repositories
Repositories now use `asyncpg` directly with raw SQL:

```python
class TransactionsRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_from_unified_event(self, event):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO transactions (...) VALUES ($1, $2, ...) RETURNING *",
                event.wallet_address,
                event.chain,
                ...
            )
            return TransactionInDB(**dict(row))
```

### Benefits
1. **Simpler** - No query builders or SQL file loaders
2. **Faster** - Direct asyncpg calls, no abstraction overhead
3. **Clearer** - SQL is visible in the code
4. **Less dependencies** - Fewer packages to maintain

## Updated Models

### Transaction Model
Updated to match `UnifiedTransactionEvent`:

**Removed fields:**
- All market data fields (volume_h24, price_change_h24, liquidity, marketcap, created_at)
- `spent_token_quantity` (replaced with `spent_token_amount`)

**New fields:**
- `received_token_quantity` (required)
- `spent_token_amount` (required)
- `price` (required)
- `liquidation` (optional JSON)
- `closed_pnl` (optional string)

## Migration

Created migration `YYYY_simplify_transactions_table.py` that:
1. Drops old market data columns
2. Adds new required columns
3. Ensures required fields are NOT NULL

**To run:**
```bash
alembic upgrade head
```

## Usage Example

```python
# Before (with aiosql)
from app.db.queries.queries import queries
row = await queries.create_new_transaction(conn, ...)

# After (direct asyncpg)
async with self.pool.acquire() as conn:
    row = await conn.fetchrow(
        "INSERT INTO transactions (...) VALUES (...) RETURNING *",
        ...
    )
```

## Migration Path

1. ✅ Updated `Transaction` model to match `UnifiedTransactionEvent`
2. ✅ Simplified `TransactionsRepository` to use asyncpg directly
3. ✅ Simplified `StrategiesRepository` to use asyncpg directly
4. ✅ Created migration to update database schema
5. ✅ Removed unused query files and base repository

## Next Steps

1. Run the migration: `alembic upgrade head`
2. Test that transactions are saved correctly
3. Remove `aiosql` and `pypika` from `pyproject.toml` if not used elsewhere
4. Update any other code that might reference the old query system

