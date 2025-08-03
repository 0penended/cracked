import asyncio
from typing import Callable

from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from app.db.events import close_db_connection, connect_to_db
from app.clients.cache import token_cache


def create_start_app_handler(
    app: FastAPI,
    settings: AppSettings,
) -> Callable:  # type: ignore
    async def start_app() -> None:
        await connect_to_db(app, settings)

        # Start background cache cleanup task
        asyncio.create_task(cache_cleanup_task())

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:  # type: ignore
    @logger.catch
    async def stop_app() -> None:
        await close_db_connection(app)

    return stop_app


async def cache_cleanup_task():
    """Background task to periodically clean up expired cache entries."""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await token_cache.cleanup_expired()

            # Log cache stats periodically
            stats = token_cache.get_stats()
            if stats["total_entries"] > 0:
                logger.info(f"Cache stats: {stats}")

        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying
