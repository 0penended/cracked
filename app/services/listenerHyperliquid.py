import asyncio
import time
from typing import Set

from hyperliquid.info import Info
from hyperliquid.utils import constants

from app.models.domain.blockchain import ChainListener, UnifiedTransactionEvent
from app.services.pipeline import CoreTransactionPipeline


class HyperliquidListener(ChainListener):
    """Hyperliquid blockchain listener using the official SDK."""

    def __init__(self, pipeline: CoreTransactionPipeline):
        self.pipeline = pipeline
        self.addresses: Set[str] = set()
        self.info: Info = Info(constants.MAINNET_API_URL)  # Uses WS under the hood

    async def subscribe_wallet(self, address: str):
        """Add a wallet address to be tracked."""
        self.addresses.add(address.lower())

    async def run(self):
        """Subscribe to userFills for each wallet and keep the loop alive."""
        try:
            print(f"[Hyperliquid] Subscribing to {len(self.addresses)} wallet(s)...")

            for addr in self.addresses:
                self.info.subscribe(
                    {"type": "userFills", "user": addr},
                    lambda msg, address=addr: asyncio.create_task(self._handle_fill(msg, address))
                )
                print(f"[Hyperliquid] Subscribed to userFills for {addr}")

            while True:
                await asyncio.sleep(3600)  # Keep alive

        except Exception as e:
            print(f"[Hyperliquid] Listener error: {e}")

    async def _handle_fill(self, msg: dict, wallet: str):
        """Handle individual UserFill event."""
        try:
            fill = msg.get("data")
            if not fill:
                return

            event = UnifiedTransactionEvent(
                chain="hyperliquid",
                wallet=wallet,
                tx_hash=fill.get("hash"),
                timestamp=fill.get("timestamp", int(time.time() * 1000)),
                symbol=fill.get("symbol"),
                action="BUY" if fill.get("side") == "A" else "SELL",
                amount=float(fill.get("sz", 0)),
                price=float(fill.get("px", 0)),
                metadata=fill
            )

            await self.pipeline.handle_event(event)

        except Exception as e:
            print(f"[Hyperliquid] Error handling fill for {wallet}: {e}")