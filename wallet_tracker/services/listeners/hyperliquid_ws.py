"""WebSocket connection management for Hyperliquid listener.

Simplified connection management with:
- Automatic reconnection on failure
- Heartbeat monitoring (reconnects if no events for 5 minutes)
- Thread-safe message handling
"""

import asyncio
import time
import random
from typing import Optional, Callable
from loguru import logger

from hyperliquid.info import Info
from hyperliquid.utils.types import UserFillsSubscription


class HyperliquidWebSocketManager:
    """Manages Hyperliquid WebSocket connection, reconnection, and heartbeat."""

    # Constants
    HEARTBEAT_INTERVAL = 30  # Check every 30 seconds
    STALE_CONNECTION_THRESHOLD = 300  # 5 minutes in seconds
    MAX_BACKOFF = 60  # Maximum backoff time in seconds
    INITIAL_BACKOFF = 1  # Initial backoff time in seconds

    def __init__(self, on_message: Callable[[dict, str], None], api_url: str):
        """
        Initialize WebSocket manager.

        Args:
            on_message: Async callback function(msg: dict, wallet: str) called when message received
            api_url: Hyperliquid API URL (mainnet or testnet)
        """
        self.on_message = on_message
        self.api_url = api_url
        self.info: Optional[Info] = None
        self.addresses: set[str] = set()
        self._running = False
        self._stop_event = asyncio.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._last_event_ts: Optional[float] = None
        self._backoff_seconds = self.INITIAL_BACKOFF

    def subscribe_wallets(self, addresses: list[str]) -> None:
        """Subscribe to wallet addresses for monitoring."""
        self.addresses.update(addresses)

    async def start(self) -> None:
        """Start the WebSocket connection and monitoring."""
        self._loop = asyncio.get_running_loop()
        self._running = True
        
        # Initial connection
        await self._connect_and_subscribe()
        
        # Start heartbeat watchdog
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Wait for stop signal
        await self._stop_event.wait()

    def stop(self) -> None:
        """Stop the WebSocket connection gracefully."""
        self._running = False
        self._stop_event.set()
        
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        
        if self.info:
            try:
                self.info.disconnect_websocket()
            except Exception:
                pass

    def get_status(self) -> dict:
        """Return connection status."""
        return {
            "running": self._running,
            "subscribed_wallets": list(self.addresses),
            "last_event_ts": self._last_event_ts,
        }

    def _handle_fill_sync(self, msg: dict, wallet: str) -> None:
        """Handle WebSocket message synchronously - schedule async processing."""
        try:
            # Update last event timestamp
            self._last_event_ts = time.time()

            # Schedule async processing using the stored event loop
            if self._loop and self._loop.is_running():
                # Schedule the coroutine to run in the event loop
                # The Hyperliquid SDK calls this from a different thread, so we need thread-safe scheduling
                self._loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.on_message(msg, wallet))
                )
            else:
                logger.warning("Event loop not available for scheduling async task")

        except Exception as e:
            logger.error(f"❌ Error handling fill for {wallet}: {e}")

    async def _connect_and_subscribe(self) -> None:
        """Establish WebSocket connection and subscribe to all wallets."""
        # Disconnect existing if present
        if self.info:
            try:
                self.info.disconnect_websocket()
            except Exception:
                pass

        # Create fresh client and subscribe
        self.info = Info(self.api_url, skip_ws=False)
        logger.info(f"🔗 Connecting to Hyperliquid ({self.api_url}) and subscribing to {len(self.addresses)} wallets")

        # Subscribe to each wallet - use default argument to avoid lambda closure bug
        for addr in self.addresses:
            subscription = UserFillsSubscription(type="userFills", user=addr)
            # Default argument in lambda prevents closure bug (all lambdas would use last 'addr' otherwise)
            self.info.subscribe(
                subscription,
                lambda msg, address=addr: self._handle_fill_sync(msg, address)
            )

        # Reset backoff and initialize timestamp on successful connection
        self._backoff_seconds = self.INITIAL_BACKOFF
        self._last_event_ts = time.time()  # Initialize so we don't immediately reconnect
        logger.info("✅ Hyperliquid WebSocket connected and subscribed")

    async def _reconnect_with_backoff(self) -> None:
        """Reconnect with exponential backoff and jitter."""
        while self._running and not self._stop_event.is_set():
            try:
                await self._connect_and_subscribe()
                return  # Success - exit retry loop
            except Exception as e:
                logger.error(f"❌ Hyperliquid connection error: {e}")
                
                # Calculate sleep time with exponential backoff and jitter
                sleep_time = min(self.MAX_BACKOFF, self._backoff_seconds)
                jitter = random.uniform(0, 0.3 * sleep_time)
                total_sleep = sleep_time + jitter
                
                logger.info(f"⏳ Retrying connection in {total_sleep:.1f}s (backoff: {self._backoff_seconds}s)")
                await asyncio.sleep(total_sleep)
                
                # Exponential backoff: double the time, up to max
                self._backoff_seconds = min(self.MAX_BACKOFF, self._backoff_seconds * 2)

    async def _heartbeat_loop(self) -> None:
        """Periodic watchdog - reconnects if no events received for 5 minutes."""
        try:
            while self._running and not self._stop_event.is_set():
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)
                
                if self._stop_event.is_set():
                    break

                # Check if connection is stale (no events for 5 minutes)
                # Only check if we have a timestamp (connection was established)
                if self._last_event_ts is None:
                    continue  # Haven't connected yet, skip check
                
                now = time.time()
                time_since_last_event = now - self._last_event_ts
                
                if time_since_last_event > self.STALE_CONNECTION_THRESHOLD:
                    logger.warning(
                        f"⚠️ No events received for {time_since_last_event:.0f}s (> {self.STALE_CONNECTION_THRESHOLD}s). Reconnecting..."
                    )
                    await self._reconnect_with_backoff()
                    # Reset timestamp after successful reconnection (will be updated when next event arrives)
                    self._last_event_ts = time.time()
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Hyperliquid heartbeat error: {e}")
