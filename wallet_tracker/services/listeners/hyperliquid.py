import time
from typing import Optional, Set
from loguru import logger

from wallet_tracker.services.listeners.base import ChainListener
from wallet_tracker.services.processor import TransactionProcessor
from wallet_tracker.services.listeners.hyperliquid_ws import HyperliquidWebSocketManager
from wallet_tracker.models.domain.unified_transaction_event import UnifiedTransactionEvent, UnifiedTransactionEventLiquidation, Action, SUPPORTED_ACTIONS


class HyperliquidListener(ChainListener):
    """Hyperliquid blockchain listener.

    Handles message parsing and delegates WebSocket management to HyperliquidWebSocketManager.
    """

    def __init__(self, processor: TransactionProcessor, api_url: str):
        """
        Initialize Hyperliquid listener.

        Args:
            processor: Transaction processor for handling events
            api_url: Hyperliquid API URL (mainnet or testnet)
        """
        self.processor = processor
        self.addresses: Set[str] = set()
        # WebSocket manager handles all connection complexity
        self._ws_manager = HyperliquidWebSocketManager(on_message=self._handle_message, api_url=api_url)

    def subscribe_wallets(self, addresses: list[str]) -> None:
        """Subscribe to wallet addresses for monitoring."""
        for addr in addresses:
            self.addresses.add(addr)
        self._ws_manager.subscribe_wallets(addresses)

    async def run(self) -> None:
        """Start the listener - delegates to WebSocket manager."""
        try:
            await self._ws_manager.start()
        except Exception as e:
            logger.error(f"❌ Hyperliquid listener error: {e}")

    def stop(self) -> None:
        """Stop the listener gracefully."""
        self._ws_manager.stop()

    def get_status(self) -> dict:
        """Return listener status."""
        return self._ws_manager.get_status()

    async def _handle_message(self, msg: dict, wallet: str) -> None:
        """Handle incoming WebSocket message - parse and process."""
        try:
            # Parse message to UnifiedTransactionEvent
            event = await self._parse_message(msg, wallet)
            if event:
                # Process through processor (handles filtering, saving, evaluation, alerting)
                await self.processor.process(event)
            else:
                logger.debug(f"Failed to create event for {wallet}")
        except Exception as e:
            logger.error(f"❌ Error processing message for {wallet}: {e}")

    async def _parse_message(
        self, msg: dict, wallet: str
    ) -> Optional[UnifiedTransactionEvent]:
        """Parse Hyperliquid websocket message to UnifiedTransactionEvent."""
        try:
            data = msg.get("data")
            if not data:
                logger.debug(f"[Hyperliquid] No data in message for {wallet}")
                return None

            # Get fills list from data
            fills = data.get("fills")
            if not fills or not isinstance(fills, list) or len(fills) == 0:
                logger.debug(f"[Hyperliquid] No fills in data for {wallet}")
                return None

            # Process only the first fill
            fill = fills[0]

            # Extract required fields
            coin = fill.get("coin")
            if not coin:
                logger.debug(f"[Hyperliquid] No coin in fill for {wallet}")
                return None

            def _round_value(value: float) -> float:
                """Round value to 2 decimals if >= 0.01, otherwise return as-is."""
                if value >= 0.01:
                    return round(value, 2)
                return value

            try:
                price = float(fill.get("px", 0))
                quantity = float(fill.get("sz", 0))
            except (ValueError, TypeError) as e:
                logger.debug(f"[Hyperliquid] Invalid price/quantity in fill for {wallet}: {e}")
                return None

            if price <= 0 or quantity <= 0:
                logger.debug(f"[Hyperliquid] Invalid price or quantity for {wallet}")
                return None

            # Round all values before creating event
            transaction_value_usd = _round_value(price * quantity)

            # Extract other fields
            timestamp = fill.get("time", int(time.time() * 1000))
            tx_hash = fill.get("hash", "")
            direction = fill.get("dir", "")
            closed_pnl = fill.get("closedPnl")
            liquidation_data = fill.get("liquidation")

            # Map direction to Action enum (using SUPPORTED_ACTIONS as single source of truth)
            action_map = {
                "Buy": Action.BUY,
                "Sell": Action.SELL,
                "Open Long": Action.OPEN_LONG,
                "Close Long": Action.CLOSE_LONG,
                "Open Short": Action.OPEN_SHORT,
                "Close Short": Action.CLOSE_SHORT,
            }

            action = action_map.get(direction)
            if not action or action not in SUPPORTED_ACTIONS:
                logger.debug(f"[Hyperliquid] Unknown or unsupported direction '{direction}' for {wallet}")
                return None

            # Determine received and spent assets based on action (only SUPPORTED_ACTIONS)
            # All values are already rounded before this point
            if action == Action.BUY:
                # Buy: receive coin, spend USDC
                received_symbol = coin
                received_quantity = quantity
                received_price = price
                spent_symbol = "USDC"
                spent_amount = transaction_value_usd
                spent_price = 1.0
            elif action == Action.SELL:
                # Sell: receive USDC, spend coin
                received_symbol = "USDC"
                received_quantity = transaction_value_usd
                received_price = 1.0
                spent_symbol = coin
                spent_amount = quantity
                spent_price = price
            elif action == Action.OPEN_LONG:
                # Opening long: receive coin, spend USDC
                received_symbol = coin
                received_quantity = quantity
                received_price = price
                spent_symbol = "USDC"
                spent_amount = transaction_value_usd
                spent_price = 1.0
            elif action == Action.CLOSE_LONG:
                # Closing long: receive USDC, spend coin
                received_symbol = "USDC"
                received_quantity = transaction_value_usd
                received_price = 1.0
                spent_symbol = coin
                spent_amount = quantity
                spent_price = price
            elif action == Action.OPEN_SHORT:
                # Opening short: receive USDC (collateral), spend coin (shorting)
                received_symbol = "USDC"
                received_quantity = transaction_value_usd
                received_price = 1.0
                spent_symbol = coin
                spent_amount = quantity
                spent_price = price
            elif action == Action.CLOSE_SHORT:
                # Closing short: receive coin (buying back), spend USDC
                received_symbol = coin
                received_quantity = quantity
                received_price = price
                spent_symbol = "USDC"
                spent_amount = transaction_value_usd
                spent_price = 1.0
            else:
                logger.debug(f"[Hyperliquid] Unhandled action {action} for {wallet}")
                return None

            # Parse liquidation if present
            liquidation = None
            if liquidation_data:
                liquidation = UnifiedTransactionEventLiquidation(
                    markPx=liquidation_data.get("markPx", 0.0),
                    method=liquidation_data.get("method", "market"),
                    liquidatedUser=liquidation_data.get("liquidatedUser"),
                )

            # Create unified event
            return UnifiedTransactionEvent(
                chain="hyperliquid",
                wallet_address=wallet,
                txn_hash=tx_hash,
                timestamp=timestamp,
                action=action,
                received_token_symbol=received_symbol,
                received_token_quantity=received_quantity,
                received_token_price=received_price,
                spent_token_symbol=spent_symbol,
                spent_token_quantity=spent_amount,
                spent_token_price=spent_price,
                transaction_value_usd=transaction_value_usd,
                liquidation=liquidation,
                closed_pnl=closed_pnl,
                # Note: token IDs not available in fill data, leaving as None
            )

        except Exception as e:
            logger.error(f"[Hyperliquid] Error parsing message for {wallet}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
