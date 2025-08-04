import asyncio
import time
from typing import Set

from hyperliquid.info import Info
from hyperliquid.utils import constants

from app.services.listeners.base import ChainListener
from app.services.pipeline.core import CoreTransactionPipeline
from app.clients.CoinMarketCapClient import CoinMarketCapClient
from app.services.fetchers.hyperliquid import HyperliquidTransactionFetcher


class HyperliquidListener(ChainListener):
    """Hyperliquid blockchain listener using the official SDK.
    Simple, efficient implementation for monitoring wallets.
    """

    def __init__(
        self,
        pipeline: CoreTransactionPipeline,
        transaction_fetcher: HyperliquidTransactionFetcher,
    ):
        self.pipeline = pipeline
        self.transaction_fetcher = transaction_fetcher
        self.addresses: Set[str] = set()
        self.info: Info = Info(constants.MAINNET_API_URL)  # Uses WS under the hood
        self.loop = asyncio.get_event_loop()

    def subscribe_wallets(self, addresses: list[str]):
        """Add a wallet address to be tracked."""
        for addr in addresses:
            self.addresses.add(addr)

    async def run(self):
        """Subscribe to userFills for each wallet and keep the loop alive."""
        try:
            for addr in self.addresses:
                self.info.subscribe(
                    {"type": "userFills", "user": addr},
                    lambda msg, address=addr: asyncio.run_coroutine_threadsafe(
                        self._handle_fill(msg, address), self.loop
                    ),
                )

            while True:
                await asyncio.sleep(3600)  # Keep alive

        except Exception as e:
            print(f"[Hyperliquid] Listener error: {e}")

    async def _handle_fill(self, msg: dict, wallet: str):
        """Handle individual UserFill event."""
        try:
            # Extract transaction hash
            tx_hash = self._get_tx_hash(msg)

            if not tx_hash:
                print(f"[Hyperliquid] No transaction hash found for {wallet}")
                return

            # Check database (persistent across restarts)
            if await self.pipeline.db_writer.transaction_exists(tx_hash):
                # Skip duplicate transaction - no need for verbose logging
                return

            # Use the transaction fetcher to parse and create the event
            event = await self.transaction_fetcher.parse_and_create_event(msg, wallet)

            if event:
                await self.pipeline.handle_event(event)
            else:
                print(f"[Hyperliquid] Failed to create event for {wallet}")

        except Exception as e:
            print(f"[Hyperliquid] Error handling fill for {wallet}: {e}")
            import traceback

            traceback.print_exc()

    def _get_tx_hash(self, msg: dict) -> str:
        """Extract transaction hash from the websocket message."""
        try:
            data = msg.get("data", {})
            if not data:
                return ""

            fills = data.get("fills", [])
            if not fills or len(fills) == 0:
                return ""

            # Get the first fill's hash
            fill = fills[0]
            return fill.get("hash", "")

        except Exception as e:
            print(f"[Hyperliquid] Error extracting transaction hash: {e}")
            return ""
