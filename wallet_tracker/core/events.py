"""Wallet tracker lifecycle event handlers."""

import asyncio
import asyncpg
from fastapi import FastAPI
from loguru import logger

from wallet_tracker.core.settings.app import AppSettings
from wallet_tracker.services.blockchain_monitor_service import BlockchainMonitorService


async def start_wallet_tracker_services(
    app: FastAPI,
    settings: AppSettings,
    db_pool: asyncpg.Pool,
) -> None:
    """
    Start wallet_tracker services (blockchain monitoring).
    
    Note: Database connection must be established before calling this.
    The db_pool should already be in app.state.db_pool.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
        db_pool: Database connection pool (must already be created)
    """
    try:
        blockchain_service = BlockchainMonitorService(settings)
        app.state.blockchain_service = blockchain_service
        asyncio.create_task(blockchain_service.start(db_pool=db_pool))
        logger.info("✅ Blockchain monitoring service started")
    except Exception as e:
        logger.error(f"❌ Failed to start blockchain monitoring: {e}")
        # Don't fail the entire app startup if blockchain monitoring fails
        # The app can still serve API endpoints


async def stop_wallet_tracker_services(app: FastAPI) -> None:
    """
    Stop wallet_tracker services (blockchain monitoring).
    
    Note: This does NOT close the database connection.
    The database connection should be closed separately in the main app.
    
    Args:
        app: FastAPI application instance
    """
    if hasattr(app.state, "blockchain_service"):
        await app.state.blockchain_service.stop()
        logger.info("✅ Blockchain monitoring service stopped")
