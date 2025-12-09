import asyncio
import asyncpg
from typing import Optional
from loguru import logger

from wallet_tracker.core.settings.app import AppSettings

from wallet_tracker.services.processor import TransactionProcessor
from wallet_tracker.services.alerts import TelegramAlertSender
from wallet_tracker.services.listeners.hyperliquid import HyperliquidListener
from wallet_tracker.services.utils.activity_limiter import WalletActivityLimiter
from wallet_tracker.clients.TelegramClient import TelegramClient
from wallet_tracker.db.repositories.transactions import TransactionsRepository
from wallet_tracker.db.repositories.strategies import StrategiesRepository
from wallet_tracker.constants.wallets import get_hyperliquid_addresses


class BlockchainMonitorService:
    """Service to run blockchain monitoring as a background task."""

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.db_conn: Optional[asyncpg.Connection] = None
        self.strategies_repository: Optional[StrategiesRepository] = None
        self.transaction_repository: Optional[TransactionsRepository] = None
        self.telegram_client: Optional[TelegramClient] = None
        self.hyperliquid_listener: Optional[HyperliquidListener] = None
        self._running = False

    async def start(self, db_pool: asyncpg.Pool | None = None) -> None:
        """
        Start the blockchain monitoring service.

        Args:
            db_pool: Optional shared database pool. If None, creates its own.
        """
        if self._running:
            logger.warning("Blockchain monitoring service is already running")
            return

        logger.info("🚀 Starting blockchain monitoring service...")

        try:
            # Use shared pool if provided, otherwise create own
            if db_pool:
                self.db_pool = db_pool
                self._using_shared_pool = True
                logger.info("Using shared database connection pool")
            else:
                # Fallback: create own pool if not provided
                import asyncpg
                self.db_pool = await asyncpg.create_pool(
                    self.settings.database_url, min_size=5, max_size=20
                )
                self._using_shared_pool = False
                logger.info("Created dedicated database connection pool")
            self.strategies_repository = StrategiesRepository(self.db_pool)
            self.transaction_repository = TransactionsRepository(self.db_pool)
            self.telegram_client = TelegramClient(self.settings.telegram_bot_token)

            # TODO: add strategies if we want to alert on thresholds
            hyperliquid_strategies = []

            processor_hyperliquid = TransactionProcessor(
                transaction_repo=self.transaction_repository,
                strategies_repo=self.strategies_repository,
                strategies=hyperliquid_strategies,
                alert_sender=TelegramAlertSender(
                    telegram_client=self.telegram_client,
                    chat_id=self.settings.telegram_chat_id,
                    chain_name="Hyperliquid",
                ),
                should_alert=lambda results: len(results) >= 2,
                activity_limiter=WalletActivityLimiter(
                    activity_window_seconds=60,
                    max_tx_per_window=15,
                ),
                min_transaction_value=self.settings.min_transaction_value,
            )
            self.hyperliquid_listener = HyperliquidListener(
                processor=processor_hyperliquid,
                api_url=self.settings.hyperliquid_api_url,
            )
            self.hyperliquid_listener.subscribe_wallets(get_hyperliquid_addresses())
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
        # Close database connection pool only if we created it ourselves
        # (if using shared pool, don't close it here)
        if self.db_pool and not hasattr(self, '_using_shared_pool'):
            await self.db_pool.close()
            self.db_pool = None

        logger.info("✅ Blockchain monitoring service stopped")

    async def _run_monitoring(self) -> None:
        """Run the monitoring loop."""
        try:
            # Start listener
            if self.hyperliquid_listener:
                await self.hyperliquid_listener.run()
                logger.info("✅ Hyperliquid listener started")

        except asyncio.CancelledError:
            logger.info("🛑 Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            # Mark listener as not running on fatal loop error
            if self.hyperliquid_listener:
                self.hyperliquid_listener._running = False
            raise
        finally:
            logger.info("🛑 Monitoring loop stopped")

    @property
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._running

    def get_status(self) -> dict:
        hl_status = (
            self.hyperliquid_listener.get_status()
            if self.hyperliquid_listener
            else None
        )
        return {
            "service_running": self._running,
            "hyperliquid": hl_status,
        }
