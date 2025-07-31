import asyncio
import time
from typing import Optional, Dict, Any

from app.clients.CoinMarketCapClient import CoinMarketCapClient
from app.models.domain.blockchain import UnifiedTransactionEvent, Action


class HyperliquidTransactionFetcher:
    """Handles parsing Hyperliquid websocket messages and creating unified events."""

    def __init__(self, coinmarketcap_client: CoinMarketCapClient):
        self.coinmarketcap_client = coinmarketcap_client

    async def parse_and_create_event(
        self, msg: dict, wallet: str
    ) -> Optional[UnifiedTransactionEvent]:
        """Parse a Hyperliquid websocket message and create a UnifiedTransactionEvent."""
        try:
            print(f"[Hyperliquid] {msg}")
            data = msg.get("data")
            if not data:
                print(f"[Hyperliquid] No data in message for {wallet}")
                return None

            # Get fills list from data
            fills = data.get("fills")
            if not fills or not isinstance(fills, list) or len(fills) == 0:
                print(f"[Hyperliquid] No fills in data for {wallet}")
                return None

            # Process the first fill (you can extend this to handle multiple fills if needed)
            fill = fills[0]

            # Extract basic trade information with validation
            symbol = fill.get("coin")  # Changed from "symbol" to "coin"
            if not symbol:
                print(f"[Hyperliquid] No coin in fill data for {wallet}")
                return None

            # Get the direction field which directly maps to Action
            direction = fill.get("dir")
            if not direction:
                print(f"[Hyperliquid] No direction in fill data for {wallet}")
                return None

            try:
                price = float(fill.get("px", 0))
                quantity = float(fill.get("sz", 0))
            except (ValueError, TypeError):
                print(f"[Hyperliquid] Invalid price or quantity for {wallet}")
                return None

            if price <= 0 or quantity <= 0:
                print(
                    f"[Hyperliquid] Invalid price ({price}) or quantity ({quantity}) for {wallet}"
                )
                return None

            timestamp = fill.get("time", int(time.time() * 1000))
            tx_hash = fill.get("hash", "")

            # Map direction directly to Action
            action_map = {
                "Buy": Action.BUY,
                "Sell": Action.SELL,
                "Open Long": Action.OPEN_LONG,
                "Close Long": Action.CLOSE_LONG,
                "Open Short": Action.OPEN_SHORT,
                "Close Short": Action.CLOSE_SHORT,
            }

            action = action_map.get(direction)
            if not action:
                print(f"[Hyperliquid] Unknown direction '{direction}' for {wallet}")
                return None

            # Determine received and spent assets based on action
            if action in [Action.BUY, Action.OPEN_LONG]:
                # Buying the asset
                received_symbol = symbol
                received_amount = quantity
                spent_symbol = "USDC"
                spent_amount = quantity * price
            elif action in [Action.SELL, Action.CLOSE_LONG]:
                # Selling the asset
                received_symbol = "USDC"
                received_amount = quantity * price
                spent_symbol = symbol
                spent_amount = quantity
            elif action in [Action.OPEN_SHORT]:
                # Opening short position
                received_symbol = "USDC"
                received_amount = quantity * price
                spent_symbol = symbol
                spent_amount = quantity
            elif action in [Action.CLOSE_SHORT]:
                # Closing short position
                received_symbol = symbol
                received_amount = quantity
                spent_symbol = "USDC"
                spent_amount = quantity * price
            else:
                # Default case
                received_symbol = symbol
                received_amount = quantity
                spent_symbol = "USDC"
                spent_amount = quantity * price

            return await self._create_unified_event(
                action=action,
                received_symbol=received_symbol,
                received_amount=received_amount,
                spent_symbol=spent_symbol,
                spent_amount=spent_amount,
                price=price,
                chain="hyperliquid",
                wallet=wallet,
                tx_hash=tx_hash,
                timestamp=timestamp,
            )

        except Exception as e:
            print(f"[Hyperliquid] Error parsing message for {wallet}: {e}")
            import traceback

            traceback.print_exc()
            return None

    async def _create_unified_event(
        self,
        action: Action,
        received_symbol: str,
        received_amount: float,
        spent_symbol: str,
        spent_amount: float,
        price: float,
        chain: str,
        wallet: str,
        tx_hash: str,
        timestamp: int,
    ) -> UnifiedTransactionEvent:
        """Create a UnifiedTransactionEvent with market data from CoinMarketCap."""

        # Collect symbols to fetch market data for (excluding USDC)
        symbols_to_fetch = []
        if received_symbol != "USDC":
            symbols_to_fetch.append(received_symbol)
        if spent_symbol != "USDC":
            symbols_to_fetch.append(spent_symbol)

        # Fetch market data from CoinMarketCap
        market_data = {}
        if symbols_to_fetch:
            try:
                prices_data = self.coinmarketcap_client.get_prices(symbols_to_fetch)
                if prices_data:
                    # The response structure has numeric keys, so we need to find the right data
                    for symbol in symbols_to_fetch:
                        for key, data in prices_data.items():
                            if data.get("symbol") == symbol:
                                market_data[symbol] = data
                                break
            except Exception as e:
                print(f"[Hyperliquid] Error fetching market data: {e}")

        # Extract market data for received token
        received_volume_h24 = 0.0
        received_price_change_h24 = 0.0
        received_liquidity = 0.0
        received_created_at = 0

        if received_symbol != "USDC" and received_symbol in market_data:
            quote_data = market_data[received_symbol].get("quote", {}).get("USD", {})
            received_volume_h24 = float(quote_data.get("volume_24h", 0))
            received_price_change_h24 = float(quote_data.get("percent_change_24h", 0))
            # For liquidity, we'll use market cap as a proxy since CMC doesn't provide liquidity directly
            received_liquidity = float(quote_data.get("market_cap", 0))
            received_created_at = int(
                market_data[received_symbol]
                .get("date_added", "2010-01-01T00:00:00.000Z")
                .replace("T", " ")
                .replace("Z", "")
                .split(" ")[0]
                .replace("-", "")
            )

        # Extract market data for spent token
        spent_volume_h24 = 0.0
        spent_price_change_h24 = 0.0
        spent_liquidity = 0.0
        spent_created_at = 0

        if spent_symbol != "USDC" and spent_symbol in market_data:
            quote_data = market_data[spent_symbol].get("quote", {}).get("USD", {})
            spent_volume_h24 = float(quote_data.get("volume_24h", 0))
            spent_price_change_h24 = float(quote_data.get("percent_change_24h", 0))
            # For liquidity, we'll use market cap as a proxy since CMC doesn't provide liquidity directly
            spent_liquidity = float(quote_data.get("market_cap", 0))
            spent_created_at = int(
                market_data[spent_symbol]
                .get("date_added", "2010-01-01T00:00:00.000Z")
                .replace("T", " ")
                .replace("Z", "")
                .split(" ")[0]
                .replace("-", "")
            )

        # Create UnifiedTransactionEvent
        event = UnifiedTransactionEvent(
            chain=chain,
            wallet_address=wallet,
            txn_hash=tx_hash,
            timestamp=timestamp,
            action=action,
            recieved_token_id=None,  # Hyperliquid doesn't provide contract addresses
            recieved_token_symbol=received_symbol,
            recieved_token_quantity=received_amount,
            recieved_token_price=price if received_symbol != "USDC" else 1.0,
            recieved_token_volume_h24=received_volume_h24,
            recieved_token_price_change_h24=received_price_change_h24,
            recieved_token_liquidity=received_liquidity,
            recieved_token_created_at=received_created_at,
            spent_token_id=None,  # Hyperliquid doesn't provide contract addresses
            spent_token_symbol=spent_symbol,
            spent_token_amount=spent_amount,
            spent_token_price=price if spent_symbol != "USDC" else 1.0,
            spent_token_volume_h24=spent_volume_h24,
            spent_token_price_change_h24=spent_price_change_h24,
            spent_token_liquidity=spent_liquidity,
            spent_token_created_at=spent_created_at,
        )

        print(
            f"[Hyperliquid] Created event: {action} {received_amount} {received_symbol} for {spent_amount} {spent_symbol}"
        )
        return event
