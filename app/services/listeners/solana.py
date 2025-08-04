import asyncio
from typing import Set, Callable

from solders.rpc.responses import LogsNotification
from solders.pubkey import Pubkey
from solana.rpc.websocket_api import (
    connect as ws_connect,
    RpcTransactionLogsFilterMentions,
)

from app.services.listeners.base import ChainListener
from app.services.fetchers.solana import SolanaTransactionFetcher
from app.services.pipeline.core import CoreTransactionPipeline


class SolanaListener(ChainListener):
    """Handles WebSocket connections and event routing for Solana blockchain."""

    def __init__(
        self,
        ws_url: str,
        transaction_fetcher: SolanaTransactionFetcher,
        pipeline_handler: CoreTransactionPipeline,
    ):
        self.ws_url = ws_url
        self.transaction_fetcher = transaction_fetcher
        self.pipeline_handler = pipeline_handler
        self.addresses: Set[str] = set()
        self.recent_signatures: Set[str] = set()
        self.conn = None

    def subscribe_wallets(self, addresses: list[str]):
        """Subscribe to wallet addresses for monitoring."""
        for addr in addresses:
            self.addresses.add(addr)

    async def run(self):
        """Start the WebSocket connection and monitor for transactions."""
        self.conn = await ws_connect(self.ws_url)
        print("[Solana] Connected to WebSocket.")

        # Subscribe to logs for each address
        for address in self.addresses:
            pk = Pubkey.from_string(address)
            await self.conn.logs_subscribe(
                filter_=RpcTransactionLogsFilterMentions(pubkey=pk),
                commitment="confirmed",
            )
            print(f"[Solana] Subscribed to logs for wallet {address}")

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
                        self.recent_signatures.add(signature)
                        if len(self.recent_signatures) > 10000:
                            self.recent_signatures.pop()
                        asyncio.create_task(
                            self._handle_transaction_signature(signature)
                        )

        except Exception as e:
            print(f"[Solana] WebSocket error: {e}")
        finally:
            if self.conn:
                await self.conn.close()

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
                print(f"[Solana] Processed transaction: {signature}")
                print(f"[Solana] Event: {event}")
                # Delegate to the transaction handler
                await self.pipeline_handler.handle_event(event)
        except Exception as e:
            print(f"[Solana] Error handling transaction {signature}: {e}")
