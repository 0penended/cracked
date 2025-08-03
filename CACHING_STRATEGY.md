# Caching Strategy for External API Calls

## Overview

This document describes the caching strategy implemented to reduce API calls to external services (DexScreener and CoinMarketCap) and improve performance for websocket-based transaction monitoring.

## Problem

- Websocket listeners generate high-frequency events
- Each event requires market data (price, volume, liquidity, etc.)
- External API calls are expensive and have rate limits
- Need to minimize API overhead while maintaining data freshness

## Solution

### Cache Implementation

- **In-memory cache** with TTL (Time To Live) support
- **15-minute default TTL** for most token data
- **Thread-safe** with async/sync support
- **Automatic cleanup** of expired entries

### Cache Key Strategy

#### DexScreener

- Key format: `dexscreener:{token_mint_address}`
- Example: `dexscreener:EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`

#### CoinMarketCap

- Key format: `coinmarketcap:{symbol}:{convert_currency}`
- Example: `coinmarketcap:BTC:USD`, `coinmarketcap:ETH:USD`
- **Individual symbol caching** for maximum reuse across requests

### Data Cached

#### From DexScreener:

- Token metadata (symbol, pairs data)
- Price data (`priceUsd`)
- Volume data (`volume.h24`)
- Price change (`priceChange.h24`)
- Liquidity (`liquidity.usd`)
- Creation date (`pairCreatedAt`)

#### From CoinMarketCap:

- Price data (`quote.USD.volume_24h`, `quote.USD.percent_change_24h`)
- Market cap (used as liquidity proxy)
- Creation date (`date_added`)

### Cache Behavior

1. **Cache-First**: Check cache before making API calls
2. **Individual Symbol Caching**: Each symbol cached separately for maximum reuse
3. **Batch Optimization**: Only fetch uncached symbols from API
4. **Error Caching**: Cache error responses to avoid repeated failed calls
5. **Automatic Cleanup**: Background task removes expired entries every 5 minutes

### Performance Benefits

- **Reduced API calls**: Cache hits avoid external requests
- **Faster response times**: Cached data returns immediately
- **Rate limit protection**: Fewer API calls reduce rate limit issues
- **Cost reduction**: Lower API usage costs
- **Maximum reuse**: Individual symbol caching allows reuse across different requests

### Monitoring

- Cache statistics available via `/cache/stats` endpoint
- Logging of cache hits/misses for debugging
- Background task logs cache stats periodically

### Configuration

- Default TTL: 15 minutes (900 seconds)
- Cleanup interval: 5 minutes
- Configurable per-call TTL override

### Usage Example

```python
from app.clients.cache import token_cache

# Async usage
cached_data = await token_cache.get("dexscreener:token123")
if not cached_data:
    # Fetch from API and cache
    data = await fetch_from_api()
    await token_cache.set("dexscreener:token123", data)

# Sync usage (for CoinMarketCap client)
cached_data = token_cache.get_sync("coinmarketcap:BTC:USD")
```

### Best Practices

1. **Appropriate TTL**: Use shorter TTL for volatile data, longer for stable data
2. **Error Handling**: Cache error responses to avoid repeated failed calls
3. **Monitoring**: Monitor cache hit rates and adjust TTL as needed
4. **Memory Management**: Background cleanup prevents memory leaks

### Future Enhancements

- Redis integration for distributed caching
- Cache warming strategies
- Dynamic TTL based on token volatility
- Cache compression for large datasets
