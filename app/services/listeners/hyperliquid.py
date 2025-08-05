import asyncio
from typing import Set
from loguru import logger

from hyperliquid.info import Info
from hyperliquid.utils import constants
from hyperliquid.utils.types import UserFillsSubscription

from app.services.listeners.base import ChainListener
from app.services.pipeline.core import CoreTransactionPipeline
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
        self._running = True
        self._stop_event = asyncio.Event()
        self._loop = None

    def subscribe_wallets(self, addresses: list[str]):
        """Subscribe to wallet addresses for monitoring."""
        for addr in addresses:
            self.addresses.add(addr)

    async def run(self):
        """Subscribe to userFills for each wallet and keep the connection alive."""
        try:
            # Store the event loop for use in callbacks
            self._loop = asyncio.get_running_loop()

            logger.info(f"🔗 Subscribing to {len(self.addresses)} Hyperliquid wallets")

            for addr in self.addresses:
                subscription = UserFillsSubscription(type="userFills", user=addr)
                self.info.subscribe(
                    subscription,
                    lambda msg, address=addr: self._handle_fill_sync(msg, address),
                )

            logger.info("✅ Hyperliquid subscriptions created")

            # Wait for stop signal - much more efficient than polling
            await self._stop_event.wait()

        except Exception as e:
            logger.error(f"❌ Hyperliquid listener error: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

    def _handle_fill_sync(self, msg: dict, wallet: str):
        """Handle individual UserFill event synchronously - process immediately."""
        try:
            # Extract transaction hash
            tx_hash = self._get_tx_hash(msg)

            if not tx_hash:
                logger.warning(f"⚠️ No transaction hash found for {wallet}")
                return

            # Schedule the async task using the stored event loop
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(
                        self._process_fill_async(msg, wallet, tx_hash)
                    )
                )
            else:
                logger.warning("Event loop not available for scheduling async task")

        except Exception as e:
            logger.error(f"❌ Error handling fill for {wallet}: {e}")

    async def _process_fill_async(self, msg: dict, wallet: str, tx_hash: str):
        """Process the fill asynchronously."""
        try:
            # Use the transaction fetcher to parse and create the event
            event = await self.transaction_fetcher.parse_and_create_event(msg, wallet)

            if event:
                try:
                    await self.pipeline.handle_event(event)
                except Exception as e:
                    if (
                        "duplicate key" in str(e).lower()
                        or "unique constraint" in str(e).lower()
                    ):
                        logger.info(
                            f"🔄 Duplicate transaction detected via DB error: {tx_hash}"
                        )
                    else:
                        # Re-raise other errors
                        raise
            else:
                logger.warning(f"❌ Failed to create event for {wallet}")

        except Exception as e:
            logger.error(f"❌ Error processing fill for {wallet}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

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
            logger.error(f"❌ Error extracting transaction hash: {e}")
            return ""

    def stop(self):
        """Stop the listener gracefully."""
        self._running = False
        self._stop_event.set()  # Signal the task to stop
        if self.info:
            self.info.disconnect_websocket()
