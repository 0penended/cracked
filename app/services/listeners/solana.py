import asyncio
from typing import Optional, Set, Callable, Deque
import time

from solders.rpc.responses import LogsNotification
from solders.pubkey import Pubkey
from solana.rpc.websocket_api import (
    connect as ws_connect,
    RpcTransactionLogsFilterMentions,
)

from app.services.listeners.base import ChainListener
from app.services.fetchers.solana import SolanaTransactionFetcher
from app.services.pipeline.core import CoreTransactionPipeline
from app.services.utils.activity_limiter import WalletActivityLimiter


class SolanaListener(ChainListener):
    """Handles WebSocket connections and event routing for Solana blockchain.
    Simple, efficient implementation for monitoring 25-50 wallets.
    """

    def __init__(
        self,
        ws_url: str,
        transaction_fetcher: SolanaTransactionFetcher,
        pipeline_handler: CoreTransactionPipeline,
        max_signatures: int = 5000,
        activity_limiter: WalletActivityLimiter | None = None,
    ):
        self.ws_url = ws_url
        self.transaction_fetcher = transaction_fetcher
        self.pipeline_handler = pipeline_handler
        self.addresses: Set[str] = set()
        # Track signature order and membership for eviction correctness
        self.recent_signatures: Set[str] = set()
        self._recent_order: Deque[str] = __import__("collections").deque()
        self.max_signatures = max_signatures
        self.conn = None
        self._running = True
        self.activity_limiter = activity_limiter or WalletActivityLimiter()
        self._last_event_ts: Optional[float] = None

    def subscribe_wallets(self, addresses: list[str]):
        """Subscribe to wallet addresses for monitoring."""
        for addr in addresses:
            self.addresses.add(addr)

    def stop(self):
        """Stop the listener gracefully."""
        self._running = False
        if self.conn:
            # Schedule connection close
            asyncio.create_task(self.conn.close())

    async def run(self):
        """Start the WebSocket connection and monitor for transactions."""
        try:
            await self._connect_and_monitor()
        except Exception as e:
            print(f"[Solana] WebSocket error: {e}")
            # Only reconnect if we're still supposed to be running
            if self._running:
                print("[Solana] Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
                await self.run()  # Recursive call to reconnect
            else:
                # Mark not running if not attempting reconnect
                self._running = False

    async def _connect_and_monitor(self):
        """Connect to websocket and monitor for transactions."""
        # Connect to websocket
        self.conn = await ws_connect(self.ws_url)

        print(f"🔗 Subscribing to {len(self.addresses)} Solana wallets")
        # Subscribe to logs for each address
        for address in self.addresses:
            pk = Pubkey.from_string(address)
            await self.conn.logs_subscribe(
                filter_=RpcTransactionLogsFilterMentions(pubkey=pk),
                commitment="confirmed",
            )

        print("[Solana] WebSocket connected and subscribed")

        try:
            async for msgs in self.conn:
                if not isinstance(msgs, list):
                    msgs = [msgs]

                for msg in msgs:
                    if isinstance(msg, LogsNotification) and self._is_relevant_log(
                        msg.result.value.logs
                    ):
                        notification_value = msg.result.value
                        signature = notification_value.signature

                        if signature in self.recent_signatures:
                            continue

                        # Add to recent signatures with size limit (ordered eviction)
                        self.recent_signatures.add(signature)
                        self._recent_order.append(signature)
                        while len(self.recent_signatures) > self.max_signatures:
                            oldest = self._recent_order.popleft()
                            if oldest in self.recent_signatures:
                                self.recent_signatures.remove(oldest)

                        # Process transaction asynchronously
                        asyncio.create_task(
                            self._handle_transaction_signature(signature)
                        )

        except Exception as e:
            print(f"[Solana] WebSocket connection error: {e}")
            raise
        finally:
            if self.conn:
                try:
                    await self.conn.close()
                except Exception as e:
                    print(f"[Solana] Error closing connection: {e}")

    def _is_relevant_log(self, logs: list[str]) -> bool:
        """Check if transaction logs contain relevant keywords."""
        relevant_keywords = [
            "instruction: transfer",
            "instruction: swap",
            "swapevent",
            "dex::",
            "commission_amount",
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        ]
        return any(
            keyword.lower() in log.lower()
            for log in logs
            for keyword in relevant_keywords
        )

    async def _handle_transaction_signature(self, signature: str):
        """Handle a transaction signature by fetching and processing the transaction."""
        try:
            event = await self.transaction_fetcher.fetch_and_parse_transaction(
                signature
            )
            if event:
                wallet = event.wallet_address
                # Drop immediately if wallet is blacklisted
                if self.activity_limiter.is_blacklisted(wallet):
                    return

                # Track activity and blacklist if threshold exceeded
                txn_value = self._compute_transaction_value(event)
                if self.activity_limiter.record_and_check(
                    wallet, qualifying=txn_value < 1000
                ):
                    print(
                        "🛑 Solana: Blacklisted wallet {} due to high activity (> {}/min, sub-$1k). Ignoring further events.".format(
                            wallet, self.activity_limiter.max_tx_per_window
                        )
                    )
                    return
                # Update last event timestamp
                self._last_event_ts = time.time()
                # Delegate to the transaction handler
                await self.pipeline_handler.handle_event(event)
        except Exception as e:
            print(f"[Solana] Error handling transaction {signature}: {e}")
            # If processing throws, don't mark as dead; the stream is alive

    def get_status(self) -> dict:
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

    def _compute_transaction_value(self, event) -> float:
        try:
            action = getattr(event.action, "value", event.action)
            if action in ["BUY", "OPEN_LONG", "CLOSE_SHORT", "SHORT_TO_LONG"]:
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
