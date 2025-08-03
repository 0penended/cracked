"""
DexScreener API client for fetching token data from various DEXes.
"""

import asyncio
import httpx
from typing import List, Dict, Any
import logging
from .cache import token_cache

logger = logging.getLogger(__name__)


class DexScreenerClient:
    def __init__(self, batch_size: int = 3, delay_between_batches: float = 1.5):
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches

    async def fetch_dex_token_data_multi(
        self, mints: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch token data for multiple mint addresses with caching and rate limiting.

        Args:
            mints: List of token mint addresses

        Returns:
            List of dictionaries containing token data for each mint
        """
        results = []
        uncached_mints = []

        # Check cache first for all mints
        for mint in mints:
            cache_key = f"dexscreener:{mint}"
            cached_data = await token_cache.get(cache_key)
            if cached_data:
                results.append(cached_data)
                logger.debug(f"Cache hit for mint: {mint}")
            else:
                uncached_mints.append(mint)
                results.append(None)  # Placeholder for later replacement

        # If all data was cached, return early
        if not uncached_mints:
            logger.debug(f"All {len(mints)} mints found in cache")
            return results

        logger.debug(f"Fetching {len(uncached_mints)} uncached mints from API")

        async with httpx.AsyncClient() as client:
            # Process uncached mints in batches
            for i in range(0, len(uncached_mints), self.batch_size):
                batch = uncached_mints[i : i + self.batch_size]

                # Process current batch with exponential backoff retries
                batch_results = await self._process_batch_with_retry(batch, client)

                # Update results and cache the new data
                for j, mint in enumerate(batch):
                    result = batch_results[j]
                    cache_key = f"dexscreener:{mint}"

                    # Cache the result (even if it's an error)
                    await token_cache.set(cache_key, result)

                    # Update the results list
                    mint_index = mints.index(mint)
                    results[mint_index] = result

                # Add delay between batches if there are more batches to process
                if i + self.batch_size < len(uncached_mints):
                    await asyncio.sleep(self.delay_between_batches)

        return results

    async def _fetch_single_token(
        self, mint: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """Fetch token data for a single mint address."""
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
        response = await client.get(url)
        return response.json()

    async def _process_batch_with_retry(
        self, batch: List[str], client: httpx.AsyncClient, max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """Process a batch of tokens with exponential backoff retries."""
        for attempt in range(max_retries):
            try:
                # Process current batch
                batch_tasks = []
                for mint in batch:
                    task = self._fetch_single_token(mint, client)
                    batch_tasks.append(task)

                # Wait for current batch to complete
                batch_results = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )

                # Handle any exceptions in the batch
                processed_results = []
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        mint = batch[j]
                        logger.error(f"Failed to fetch {mint}: {result}")
                        processed_results.append(
                            {
                                "error": f"Failed to fetch {mint}: {str(result)}",
                                "mint": mint,
                            }
                        )
                    else:
                        processed_results.append(result)

                return processed_results

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Batch processing failed after {max_retries} attempts: {e}"
                    )
                    # Return error entries for the entire batch
                    return [
                        {"error": f"Failed to fetch {mint}: {str(e)}", "mint": mint}
                        for mint in batch
                    ]

                retry_delay = (2**attempt) * 1.0  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Batch attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
