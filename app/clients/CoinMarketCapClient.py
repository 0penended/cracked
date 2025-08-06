import httpx
import asyncio
import time
from typing import List, Dict, Optional, Any
import logging
from .cache import token_cache

logger = logging.getLogger(__name__)


class CoinMarketCapClient:
    def __init__(
        self, api_key: str, base_url: str = "https://pro-api.coinmarketcap.com"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests (10 requests/second)
        # Use async client with connection pooling for better performance
        self.client = httpx.AsyncClient(
            headers={
                "Accepts": "application/json",
                "X-CMC_PRO_API_KEY": self.api_key,
            },
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            timeout=httpx.Timeout(10.0),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_prices(
        self, symbols: List[str], convert: str = "USD"
    ) -> Optional[Dict[str, Any]]:
        # Check cache first for each symbol individually
        cached_data = {}
        uncached_symbols = []

        for symbol in symbols:
            cache_key = f"coinmarketcap:{symbol}:{convert}"
            cached_symbol_data = await token_cache.get(cache_key)
            if cached_symbol_data is not None:
                cached_data[symbol] = cached_symbol_data
            else:
                uncached_symbols.append(symbol)

        # If all symbols were cached, return combined data
        if not uncached_symbols:
            return cached_data

        # Fetch uncached symbols from API
        url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
        params = {
            "symbol": ",".join(uncached_symbols),
            "convert": convert,
        }

        # Rate limiting - ensure minimum time between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"[CMC] Rate limiting: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

        try:
            self.last_request_time = time.time()
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            api_data = data.get("data", {})
            print("!!!uncached_symbols!!!", uncached_symbols)
            print("!!!cached_data!!!", cached_data)
            print("!!!token_cache!!!", token_cache.get_stats().get("cache_keys"))

            # Cache each symbol individually and add to result
            for symbol in uncached_symbols:
                # Find the symbol data in the API response
                symbol_data = None
                for key, value in api_data.items():
                    if value.get("symbol") == symbol:
                        symbol_data = value
                        break

                if symbol_data:
                    cache_key = f"coinmarketcap:{symbol}:{convert}"
                    await token_cache.set(cache_key, symbol_data)
                    cached_data[symbol] = symbol_data
                else:
                    logger.warning(
                        f"No data found for symbol: {symbol} - caching empty object"
                    )
                    # Cache empty object to prevent future API calls for unsupported symbols
                    cache_key = f"coinmarketcap:{symbol}:{convert}"
                    await token_cache.set(cache_key, {})
                    cached_data[symbol] = {}

            return cached_data

        except httpx.HTTPError as e:
            logger.error(f"[CMC] HTTP error: {e}")
            return cached_data  # Return whatever we have cached
        except Exception as e:
            logger.error(f"[CMC] Unexpected error: {e}")
            return cached_data  # Return whatever we have cached
