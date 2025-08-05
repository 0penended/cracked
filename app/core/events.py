import asyncio
from typing import Callable

from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from app.db.events import close_db_connection, connect_to_db
from app.services.blockchain_monitor_service import BlockchainMonitorService


def create_start_app_handler(
    app: FastAPI,
    settings: AppSettings,
) -> Callable:  # type: ignore
    async def start_app() -> None:
        # Connect to database
        await connect_to_db(app, settings)
        # Start blockchain monitoring service
        blockchain_service = BlockchainMonitorService(settings)
        app.state.blockchain_service = blockchain_service

        try:
            asyncio.create_task(blockchain_service.start())
            logger.info("✅ FastAPI app started with blockchain monitoring")
        except Exception as e:
            logger.error(f"❌ Failed to start blockchain monitoring: {e}")
            # Don't fail the entire app startup if blockchain monitoring fails
            # The app can still serve API endpoints

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:  # type: ignore
    @logger.catch
    async def stop_app() -> None:
        # Stop blockchain monitoring service
        if hasattr(app.state, "blockchain_service"):
            await app.state.blockchain_service.stop()

        # Close database connection
        await close_db_connection(app)

        logger.info("✅ FastAPI app stopped")

    return stop_app
