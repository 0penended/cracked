import httpx
from typing import List, Dict, Optional, Any
import logging
from .cache import token_cache

logger = logging.getLogger(__name__)


class CoinMarketCapClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com"
        self.client = httpx.Client(
            headers={
                "Accepts": "application/json",
                "X-CMC_PRO_API_KEY": self.api_key,
            }
        )

    def get_prices(
        self, symbols: List[str], convert: str = "USD"
    ) -> Optional[Dict[str, Any]]:
        # Check cache first for each symbol individually
        cached_data = {}
        uncached_symbols = []

        for symbol in symbols:
            cache_key = f"coinmarketcap:{symbol}:{convert}"
            cached_symbol_data = token_cache.get_sync(cache_key)
            if cached_symbol_data:
                cached_data[symbol] = cached_symbol_data
                logger.debug(f"Cache hit for symbol: {symbol}")
            else:
                uncached_symbols.append(symbol)
                logger.debug(f"Cache miss for symbol: {symbol}")

        # If all symbols were cached, return combined data
        if not uncached_symbols:
            logger.debug(f"All {len(symbols)} symbols found in cache")
            return cached_data

        logger.debug(f"Fetching {len(uncached_symbols)} uncached symbols from API")

        # Fetch uncached symbols from API
        url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
        params = {
            "symbol": ",".join(uncached_symbols),
            "convert": convert,
        }

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            api_data = data.get("data", {})

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
                    token_cache.set_sync(cache_key, symbol_data)
                    cached_data[symbol] = symbol_data
                    logger.debug(f"Cached new data for symbol: {symbol}")
                else:
                    logger.warning(f"No data found for symbol: {symbol}")

            return cached_data

        except httpx.HTTPError as e:
            logger.error(f"[CMC] HTTP error: {e}")
            return cached_data  # Return whatever we have cached
        except Exception as e:
            logger.error(f"[CMC] Unexpected error: {e}")
            return cached_data  # Return whatever we have cached
