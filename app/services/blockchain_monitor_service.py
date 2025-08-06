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
from app.constants.wallets import get_solana_addresses, get_hyperliquid_addresses


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

    async def start(self) -> None:
        """Start the blockchain monitoring service."""
        if self._running:
            logger.warning("Blockchain monitoring service is already running")
            return

        logger.info("🚀 Starting blockchain monitoring service...")

        try:
            # Create database connection pool
            self.db_pool = await asyncpg.create_pool(
                self.settings.database_url, min_size=5, max_size=20
            )
            self.strategies_repository = StrategiesRepository(self.db_pool)
            self.transaction_repository = TransactionsRepository(self.db_pool)
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
            self.hyperliquid_listener.subscribe_wallets(get_hyperliquid_addresses())

            # Solana
            solana_strategies = await SolanaStrategies.create_all(
                self.strategies_repository
            )
            solana_alert_trigger = AlertTriggerStrategyMatchQuantity(quantity=2)
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
            self.solana_listener.subscribe_wallets(get_solana_addresses())

            # Start the monitoring task
            self._running = True
            # Run monitoring in background task
            asyncio.create_task(self._run_monitoring())

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
        # Close database connection pool
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None

        logger.info("✅ Blockchain monitoring service stopped")

    async def _run_monitoring(self) -> None:
        """Run the monitoring loop."""
        try:
            # Start listeners - they can run sequentially since they're independent
            # Each listener manages its own websocket connection
            listener_tasks = []

            if self.hyperliquid_listener:
                listener_tasks.append(self.hyperliquid_listener.run())
                logger.info("✅ Hyperliquid listener started")

            if self.solana_listener:
                listener_tasks.append(self.solana_listener.run())
                logger.info("✅ Solana listener started")

            # Run all listeners concurrently - they're independent websocket connections
            await asyncio.gather(*listener_tasks, return_exceptions=True)

        except asyncio.CancelledError:
            logger.info("🛑 Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            raise
        finally:
            logger.info("🛑 Monitoring loop stopped")

    @property
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._running
