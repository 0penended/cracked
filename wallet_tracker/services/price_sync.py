import asyncio
from typing import List, Dict, Any, Set
from datetime import datetime, date
from loguru import logger

from wallet_tracker.clients.DexScreenerClient import DexScreenerClient
from wallet_tracker.clients.CoinMarketCapClient import CoinMarketCapClient
from wallet_tracker.clients.BigQueryClient import BigQueryClient
from wallet_tracker.core.settings.app import AppSettings


class TokenPriceSyncService:
    """Service to sync token prices from external APIs to BigQuery."""

    def __init__(
        self,
        dex_screener_client: DexScreenerClient,
        coinmarketcap_client: CoinMarketCapClient,
        bigquery_client: BigQueryClient,
        settings: AppSettings = None,
    ):
        self.settings = settings or AppSettings()
        self.dex_screener_client = dex_screener_client
        self.coinmarketcap_client = coinmarketcap_client
        self.bigquery_client = bigquery_client

        # BigQuery configuration - you'll need to set these in your settings
        self.positions_dataset = getattr(
            self.settings, "bigquery_positions_dataset", "your_dataset"
        )
        self.positions_table = getattr(
            self.settings, "bigquery_positions_table", "positions"
        )
        self.prices_dataset = getattr(
            self.settings, "bigquery_prices_dataset", "your_dataset"
        )
        self.prices_table = getattr(
            self.settings, "bigquery_prices_table", "coin_prices"
        )

    async def sync_all_token_prices(self) -> Dict[str, Any]:
        """Main method to sync all token prices from positions table."""
        try:
            # Step 1: Read positions from BigQuery
            positions = await self._get_positions_from_bigquery()

            # Step 2: Extract and deduplicate token addresses by exchange
            solana_tokens = self._extract_solana_tokens(positions)
            hyperliquid_tokens = self._extract_hyperliquid_tokens(positions)

            logger.info(
                f"Found {len(solana_tokens)} Solana tokens and {len(hyperliquid_tokens)} Hyperliquid tokens"
            )

            # Step 3: Fetch prices for Solana tokens from DexScreener
            solana_prices = await self._fetch_solana_prices(solana_tokens)

            # Step 4: Fetch prices for Hyperliquid tokens from CoinMarketCap
            hyperliquid_prices = await self._fetch_hyperliquid_prices(
                hyperliquid_tokens
            )

            # Step 5: Write all prices to BigQuery
            all_prices = solana_prices + hyperliquid_prices
            await self._write_prices_to_bigquery(all_prices)

            return {
                "solana_tokens_processed": len(solana_tokens),
                "hyperliquid_tokens_processed": len(hyperliquid_tokens),
                "solana_prices_fetched": len(solana_prices),
                "hyperliquid_prices_fetched": len(hyperliquid_prices),
                "total_prices_written": len(all_prices),
            }

        except Exception as e:
            logger.error(f"Error in sync_all_token_prices: {e}")
            raise

    async def _get_positions_from_bigquery(self) -> List[Dict[str, Any]]:
        """Read positions from BigQuery positions table."""
        return await self.bigquery_client.get_positions_tokens(
            self.positions_dataset, self.positions_table
        )

    def _extract_solana_tokens(self, positions: List[Dict[str, Any]]) -> Set[str]:
        """Extract unique Solana token addresses from positions."""
        solana_tokens = set()
        for position in positions:
            if position.get("exchange") == "solana" and position.get("token_ca"):
                solana_tokens.add(position["token_ca"])
        return solana_tokens

    def _extract_hyperliquid_tokens(self, positions: List[Dict[str, Any]]) -> Set[str]:
        """Extract unique Hyperliquid token symbols from positions."""
        hyperliquid_tokens = set()
        for position in positions:
            if position.get("exchange") == "hyperliquid" and position.get("token_ca"):
                # For Hyperliquid, we might need to map token_ca to symbol
                # This depends on how your data is structured
                hyperliquid_tokens.add(position["token_ca"])
        return hyperliquid_tokens

    async def _fetch_solana_prices(
        self, token_addresses: Set[str]
    ) -> List[Dict[str, Any]]:
        """Fetch prices for Solana tokens from DexScreener."""
        if not token_addresses:
            return []

        logger.info(
            f"Fetching prices for {len(token_addresses)} Solana tokens from DexScreener"
        )

        try:
            # Convert set to list for the API call
            token_list = list(token_addresses)
            metadata_list = await self.dex_screener_client.fetch_dex_token_data_multi(
                token_list
            )

            prices = []
            current_date = date.today()
            current_timestamp = datetime.now()

            for i, metadata in enumerate(metadata_list):
                if metadata and "pairs" in metadata and metadata["pairs"]:
                    pair = metadata["pairs"][0]  # Most liquid pair
                    token_address = token_list[i]

                    price_data = {
                        "token_ca": token_address,
                        "symbol": pair.get("baseToken", {}).get("symbol", "UNKNOWN"),
                        "price_date": current_date,
                        "price_usd": float(pair.get("priceUsd", 0)),
                        "price_1h_delta_pct": float(
                            pair.get("priceChange", {}).get("h1", 0)
                        ),
                        "price_24h_delta_pct": float(
                            pair.get("priceChange", {}).get("h24", 0)
                        ),
                        "volume_24h_usd": float(pair.get("volume", {}).get("h24", 0)),
                        "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
                        "market_cap_usd": 0,  # DexScreener doesn't provide market cap
                        "source": "dexscreener",
                        "last_updated": current_timestamp,
                    }
                    prices.append(price_data)

            logger.info(f"Successfully fetched {len(prices)} Solana token prices")
            return prices

        except Exception as e:
            logger.error(f"Error fetching Solana prices: {e}")
            return []

    async def _fetch_hyperliquid_prices(
        self, token_symbols: Set[str]
    ) -> List[Dict[str, Any]]:
        """Fetch prices for Hyperliquid tokens from CoinMarketCap."""
        if not token_symbols:
            return []

        logger.info(
            f"Fetching prices for {len(token_symbols)} Hyperliquid tokens from CoinMarketCap"
        )

        try:
            # Convert set to list for the API call
            symbol_list = list(token_symbols)
            prices_data = self.coinmarketcap_client.get_prices(symbol_list)

            prices = []
            current_date = date.today()
            current_timestamp = datetime.now()

            for symbol, data in prices_data.items():
                if data and "quote" in data and "USD" in data["quote"]:
                    quote = data["quote"]["USD"]

                    price_data = {
                        "token_ca": symbol,  # For Hyperliquid, token_ca might be the symbol
                        "symbol": symbol,
                        "price_date": current_date,
                        "price_usd": float(quote.get("price", 0)),
                        "price_1h_delta_pct": float(quote.get("percent_change_1h", 0)),
                        "price_24h_delta_pct": float(
                            quote.get("percent_change_24h", 0)
                        ),
                        "volume_24h_usd": float(quote.get("volume_24h", 0)),
                        "liquidity_usd": 0,  # CoinMarketCap doesn't provide liquidity
                        "market_cap_usd": float(quote.get("market_cap", 0)),
                        "source": "coinmarketcap",
                        "last_updated": current_timestamp,
                    }
                    prices.append(price_data)

            logger.info(f"Successfully fetched {len(prices)} Hyperliquid token prices")
            return prices

        except Exception as e:
            logger.error(f"Error fetching Hyperliquid prices: {e}")
            return []

    async def _write_prices_to_bigquery(self, prices: List[Dict[str, Any]]) -> None:
        """Write price data to BigQuery coin_prices table."""
        await self.bigquery_client.write_coin_prices(
            self.prices_dataset, self.prices_table, prices
        )
