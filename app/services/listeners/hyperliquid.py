import asyncio
import time
import random
from typing import Optional, Set
from loguru import logger

from hyperliquid.info import Info
from hyperliquid.utils import constants
from hyperliquid.utils.types import UserFillsSubscription

from app.services.listeners.base import ChainListener
from app.services.pipeline.core import CoreTransactionPipeline
from app.services.fetchers.hyperliquid import HyperliquidTransactionFetcher
from app.services.utils.activity_limiter import WalletActivityLimiter


class HyperliquidListener(ChainListener):
    """Hyperliquid blockchain listener using the official SDK.
    Simple, efficient implementation for monitoring wallets.
    """

    def __init__(
        self,
        pipeline: CoreTransactionPipeline,
        transaction_fetcher: HyperliquidTransactionFetcher,
        activity_limiter: WalletActivityLimiter,
    ):
        self.pipeline = pipeline
        self.transaction_fetcher = transaction_fetcher
        self.activity_limiter = activity_limiter
        self.addresses: Set[str] = set()
        self.info: Info = Info(constants.MAINNET_API_URL)  # Uses WS under the hood
        self._running = True
        self._stop_event = asyncio.Event()
        self._loop = None
        self._last_event_ts: Optional[float] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_backoff_seconds: int = 1

    def subscribe_wallets(self, addresses: list[str]):
        """Subscribe to wallet addresses for monitoring."""
        for addr in addresses:
            self.addresses.add(addr)

    async def run(self):
        """Establish connection, subscribe, and start heartbeat watchdog."""
        try:
            self._loop = asyncio.get_running_loop()
            await self._connect_and_subscribe()

            # Start heartbeat watchdog
            if not self._heartbeat_task or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Wait for stop signal - much more efficient than polling
            await self._stop_event.wait()

        except Exception as e:
            logger.error(f"❌ Hyperliquid listener error: {e}")
            self._running = False

    def _handle_fill_sync(self, msg: dict, wallet: str):
        """Handle individual UserFill event synchronously - process immediately."""
        try:
            # Drop immediately if wallet is blacklisted
            if self.activity_limiter.is_blacklisted(wallet):
                return

            # Extract transaction hash
            tx_hash = self._get_tx_hash(msg)

            if not tx_hash:
                logger.warning(f"⚠️ No transaction hash found for {wallet}")
                return

            # Update last event timestamp
            self._last_event_ts = time.time()

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
                # Record activity only for sub-$1k transactions; blacklist if exceeded
                txn_value = self._compute_transaction_value(event)
                if self.activity_limiter.record_and_check(
                    wallet, qualifying=txn_value < 1000
                ):
                    logger.info(
                        "🛑 Hyperliquid: Blacklisted wallet {} due to high activity (> {}/min, sub-$1k). Ignoring further events.".format(
                            wallet, self.activity_limiter.max_tx_per_window
                        )
                    )
                    return
                try:
                    await self.pipeline.handle_event(event)
                except Exception as e:
                    if (
                        "duplicate key" in str(e).lower()
                        or "unique constraint" in str(e).lower()
                    ):
                        pass
                    else:
                        # Re-raise other errors
                        raise
            else:
                logger.warning(f"❌ Failed to create event for {wallet}")

        except Exception as e:
            logger.error(f"❌ Error processing fill for {wallet}: {e}")

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
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        if self.info:
            self.info.disconnect_websocket()

    def get_status(self) -> dict:
        """Return a lightweight status for external health checks."""
        return {
            "running": self._running,
            "subscribed_wallets": list(
                filter(
                    lambda x: not self.activity_limiter.is_blacklisted(x),
                    self.addresses,
                )
            ),
            "last_event_ts": self._last_event_ts,
        }

    async def _connect_and_subscribe(self) -> None:
        """(Re)establish websocket connection and resubscribe to all addresses."""
        # Disconnect existing if present
        if self.info:
            try:
                self.info.disconnect_websocket()
            except Exception:
                pass

        # Create fresh client and subscribe
        self.info = Info(constants.MAINNET_API_URL)
        logger.info(f"🔗 Subscribing to {len(self.addresses)} Hyperliquid wallets")
        for addr in self.addresses:
            subscription = UserFillsSubscription(type="userFills", user=addr)
            self.info.subscribe(
                subscription,
                lambda msg, address=addr: self._handle_fill_sync(msg, address),
            )

        # Reset backoff and mark running
        self._reconnect_backoff_seconds = 1
        self._running = True

    async def _perform_reconnect(self) -> None:
        """Reconnect with exponential backoff and jitter on failure."""
        try:
            await self._connect_and_subscribe()
        except Exception as e:
            logger.error(f"❌ Hyperliquid reconnect error: {e}")
            sleep_for = min(60, self._reconnect_backoff_seconds)
            jitter = random.uniform(0, 0.3 * sleep_for)
            await asyncio.sleep(sleep_for + jitter)
            self._reconnect_backoff_seconds = min(
                60, self._reconnect_backoff_seconds * 2
            )

    async def _heartbeat_loop(self) -> None:
        """Periodic watchdog; reconnects after prolonged inactivity."""
        try:
            while self._running and not self._stop_event.is_set():
                await asyncio.sleep(30)
                if self._stop_event.is_set():
                    break

                now = time.time()
                stale = self._last_event_ts is None or (now - self._last_event_ts) > 300
                if stale:
                    logger.warning(
                        "⚠️ Hyperliquid heartbeat: no events recently; reconnecting..."
                    )
                    await self._perform_reconnect()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Hyperliquid heartbeat error: {e}")

    def _compute_transaction_value(self, event) -> float:
        """Compute transaction USD value similar to pipeline logic."""
        try:
            action = getattr(event.action, "value", event.action)
            if action in [
                "BUY",
                "OPEN_LONG",
                "CLOSE_SHORT",
                "SHORT_TO_LONG",
            ]:
                return round(
                    float(event.spent_token_amount) * float(event.spent_token_price), 2
                )
            else:
                return round(
                    float(event.received_token_quantity)
                    * float(event.received_token_price),
                    2,
                )
        except Exception:
            return 0.0
