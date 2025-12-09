# Hyperliquid Listener Architecture

## Overview

The Hyperliquid listener monitors wallet transactions on Hyperliquid exchange using WebSocket connections. It handles connection management, message parsing, and event creation.

## Architecture

```
HyperliquidListener
├── HyperliquidWebSocketManager (connection management)
│   ├── WebSocket connection lifecycle
│   ├── Automatic reconnection with backoff
│   └── Heartbeat monitoring
└── Message Parsing Logic
    ├── Aggregate fills by coin
    ├── Determine action type
    └── Create UnifiedTransactionEvent
```

## Components

### 1. HyperliquidWebSocketManager (`hyperliquid_ws.py`)

**Purpose**: Encapsulates all WebSocket complexity

**Responsibilities**:
- Manage WebSocket connection lifecycle
- Handle automatic reconnection with exponential backoff
- Monitor connection health via heartbeat
- Thread-safe async task scheduling

**Key Features**:
- **Exponential Backoff**: Starts at 1s, doubles up to 60s on reconnect failures
- **Jitter**: Adds random delay (0-30% of backoff) to prevent thundering herd
- **Heartbeat**: Checks every 30s, reconnects if no events for 5 minutes
- **Thread-Safe**: Uses `call_soon_threadsafe` to schedule async tasks from sync callbacks

### 2. HyperliquidListener (`hyperliquid.py`)

**Purpose**: Parse messages and create unified events

**Responsibilities**:
- Parse Hyperliquid WebSocket messages
- Aggregate multiple fills by coin
- Create `UnifiedTransactionEvent` objects
- Send events to processor

## Message Flow

```
WebSocket Message
    ↓
_handle_fill_sync() [sync callback from Hyperliquid SDK]
    ↓
Schedule async task via event loop
    ↓
_process_fill_async() [async processing]
    ↓
_parse_message() [aggregate fills, determine action]
    ↓
Create UnifiedTransactionEvent
    ↓
processor.process() [filter, save, evaluate, alert]
```

## Fill Aggregation Logic

### Problem
A single transaction can have multiple fills (partial fills, different prices, etc.)

### Solution
1. **Group by coin**: All fills for the same coin are grouped together
2. **Group by direction**: Within each coin, group by action type (Open Long, Close Long, etc.)
3. **Aggregate**: Sum quantities and values, calculate weighted average price
4. **Prioritize**: Position actions (OPEN_LONG, CLOSE_LONG) over simple BUY/SELL

### Example
```
Fills:
  - BTC, Open Long, 1.0 @ 50000 = $50,000
  - BTC, Open Long, 0.5 @ 50100 = $25,050

Aggregated:
  - BTC, Open Long, 1.5 @ $50,033.33 (weighted avg)
  - received_symbol: BTC, received_amount: 1.5
  - spent_symbol: USDC, spent_amount: $75,050
```

## Received/Spent Asset Logic

The logic determines what asset is received vs spent based on the action:

| Action | Received | Spent | Explanation |
|--------|----------|-------|-------------|
| OPEN_LONG | Coin | USDC | Buying coin with leverage |
| CLOSE_LONG | USDC | Coin | Selling long position |
| OPEN_SHORT | USDC | Coin | Shorting - receive collateral |
| CLOSE_SHORT | Coin | USDC | Closing short - buy back coin |

## Reconnection Strategy

### When Reconnection Happens
1. **Initial connection failure**: Immediate retry with backoff
2. **Heartbeat timeout**: No events for 5 minutes triggers reconnect
3. **WebSocket error**: Caught and triggers reconnect

### Backoff Algorithm
```
backoff = min(60, backoff * 2)  # Exponential, max 60s
sleep_time = backoff + random(0, 0.3 * backoff)  # Add jitter
```

### Why This Works
- **Exponential backoff**: Prevents hammering the server during outages
- **Jitter**: Prevents all clients reconnecting simultaneously
- **Heartbeat**: Detects stale connections even if WebSocket appears open

## Thread Safety

The Hyperliquid SDK uses synchronous callbacks (`_handle_fill_sync`), but we need async processing. Solution:

```python
# Sync callback from SDK
def _handle_fill_sync(msg, wallet):
    # Schedule async task on event loop
    loop.call_soon_threadsafe(
        lambda: asyncio.create_task(process_async(msg, wallet))
    )
```

This ensures:
- SDK callbacks don't block
- Async processing happens on correct event loop
- Thread-safe task scheduling

## Error Handling

- **Invalid fills**: Skipped with debug logging
- **Parse errors**: Logged, message skipped
- **Connection errors**: Trigger reconnection with backoff
- **Processing errors**: Logged, don't crash listener

## Performance Considerations

- **Single event loop**: All async tasks share one loop
- **Non-blocking callbacks**: Sync callbacks just schedule tasks
- **Efficient aggregation**: O(n) pass through fills
- **Minimal logging**: Debug level for skipped messages

## Future Improvements

1. **Multiple coins**: Currently processes first coin only
2. **Fill metadata**: Could track individual fill prices for better analytics
3. **Connection pooling**: If monitoring many wallets
4. **Rate limiting**: If needed for high-frequency wallets

