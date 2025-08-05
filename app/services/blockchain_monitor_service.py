import asyncio
import asyncpg
from typing import Optional
from loguru import logger

from app.core.settings.app import AppSettings
from app.services.pipeline.core import CoreTransactionPipeline
from app.services.listeners.solana import SolanaListener
from app.services.fetchers.solana import SolanaTransactionFetcher
from app.services.listeners.hyperliquid import HyperliquidListener
from app.services.fetchers.hyperliquid import HyperliquidTransactionFetcher
from app.clients.CoinMarketCapClient import CoinMarketCapClient
from app.clients.DexScreenerClient import DexScreenerClient
from app.clients.TelegramClient import TelegramClient
from app.services.routers.alerts.telegram import TelegramAlertRouter
from app.services.routers.alerts.triggers import AlertTriggerStrategyMatchQuantity
from app.services.routers.strategy_factory import (
    HyperliquidStrategies,
    SolanaStrategies,
)
from app.db.repositories.transactions import TransactionsRepository
from app.db.repositories.strategies import StrategiesRepository


class BlockchainMonitorService:
    """Service to run blockchain monitoring as a background task."""

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.db_conn: Optional[asyncpg.Connection] = None
        self.strategies_repository: Optional[StrategiesRepository] = None
        self.transaction_repository: Optional[TransactionsRepository] = None
        self.coinmarketcap_client: Optional[CoinMarketCapClient] = None
        self.dex_screener_client: Optional[DexScreenerClient] = None
        self.telegram_client: Optional[TelegramClient] = None
        self.solana_listener: Optional[SolanaListener] = None
        self.hyperliquid_listener: Optional[HyperliquidListener] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the blockchain monitoring service."""
        if self._running:
            logger.warning("Blockchain monitoring service is already running")
            return

        logger.info("🚀 Starting blockchain monitoring service...")

        try:
            # Create database connection
            self.db_conn = await asyncpg.connect(self.settings.database_url)
            self.strategies_repository = StrategiesRepository(self.db_conn)
            self.transaction_repository = TransactionsRepository(self.db_conn)

            # Create clients
            self.coinmarketcap_client = CoinMarketCapClient(
                api_key=self.settings.coinmarketcap_api_key,
                base_url=self.settings.coinmarketcap_base_url,
            )
            self.dex_screener_client = DexScreenerClient()
            self.telegram_client = TelegramClient(self.settings.telegram_bot_token)

            # Create Hyperliquid pipeline with type-safe strategies (auto-registered in DB)
            hyperliquid_strategies = await HyperliquidStrategies.create_all(
                self.strategies_repository
            )

            # Create alert trigger for Hyperliquid (require at least 2 strategies to match)
            hyperliquid_alert_trigger = AlertTriggerStrategyMatchQuantity(quantity=2)

            pipeline_hyperliquid = CoreTransactionPipeline(
                strategies=hyperliquid_strategies,
                alert_router=TelegramAlertRouter(
                    telegram_client=self.telegram_client,
                    chat_id=self.settings.telegram_chat_id,
                    chain_name="Hyperliquid",
                ),
                alert_trigger=hyperliquid_alert_trigger,
                strategies_repository=self.strategies_repository,
                transaction_repository=self.transaction_repository,
            )

            hyperliquid_transaction_fetcher = HyperliquidTransactionFetcher(
                coinmarketcap_client=self.coinmarketcap_client
            )
            self.hyperliquid_listener = HyperliquidListener(
                pipeline=pipeline_hyperliquid,
                transaction_fetcher=hyperliquid_transaction_fetcher,
            )
            self.hyperliquid_listener.subscribe_wallets(
                ["0x576A41Ba10520568811E1465CABb52aBfE6beAdc"]
            )

            # Create Solana pipeline with type-safe strategies (auto-registered in DB)
            solana_strategies = await SolanaStrategies.create_all(
                self.strategies_repository
            )

            # Create alert trigger for Solana (require at least 1 strategy to match)
            solana_alert_trigger = AlertTriggerStrategyMatchQuantity(quantity=3)

            pipeline_solana = CoreTransactionPipeline(
                strategies=solana_strategies,
                alert_router=TelegramAlertRouter(
                    telegram_client=self.telegram_client,
                    chat_id=self.settings.telegram_chat_id,
                    chain_name="Solana",
                ),
                alert_trigger=solana_alert_trigger,
                strategies_repository=self.strategies_repository,
                transaction_repository=self.transaction_repository,
            )

            solana_transaction_fetcher = SolanaTransactionFetcher(
                self.settings.solana_rpc_url, self.dex_screener_client
            )
            self.solana_listener = SolanaListener(
                ws_url=self.settings.solana_ws_url,
                transaction_fetcher=solana_transaction_fetcher,
                pipeline_handler=pipeline_solana,
            )
            self.solana_listener.subscribe_wallets(
                ["EgaYt5xZK4qeWphbKD42oxzbeArYkWY9WCxrQBk9F6r5"]
            )

            # Start the monitoring task
            self._running = True
            self._task = asyncio.create_task(self._run_monitoring())

            logger.info("✅ Blockchain monitoring service started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start blockchain monitoring service: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the blockchain monitoring service."""
        if not self._running:
            return

        logger.info("🛑 Stopping blockchain monitoring service...")

        self._running = False

        # Cancel the monitoring task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Close database connection
        if self.db_conn:
            await self.db_conn.close()
            self.db_conn = None

        logger.info("✅ Blockchain monitoring service stopped")

    async def _run_monitoring(self) -> None:
        """Run the monitoring loop."""
        logger.info("🔄 Starting monitoring loop...")

        try:
            # Start listeners concurrently
            tasks = []

            if self.hyperliquid_listener:
                logger.info("🔗 Starting Hyperliquid listener...")
                hyperliquid_task = asyncio.create_task(self.hyperliquid_listener.run())
                tasks.append(hyperliquid_task)
                logger.info("✅ Hyperliquid listener started")

            if self.solana_listener:
                logger.info("🔗 Starting Solana listener...")
                solana_task = asyncio.create_task(self.solana_listener.run())
                tasks.append(solana_task)
                logger.info("✅ Solana listener started")

            # Keep the service running and wait for all listeners
            while self._running:
                await asyncio.sleep(1)

            # Cancel all tasks when stopping
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            logger.info("🛑 Monitoring loop stopped")

    @property
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._running
