"""Shared database connection pool management."""

import asyncpg
from fastapi import FastAPI
from loguru import logger

from wallet_tracker.core.settings.app import AppSettings


async def create_db_pool(settings: AppSettings) -> asyncpg.Pool:
    """
    Create a shared database connection pool.

    Args:
        settings: Application settings with database URL

    Returns:
        asyncpg connection pool
    """
    logger.info("Creating shared database connection pool")
    pool = await asyncpg.create_pool(
        str(settings.database_url),
        min_size=settings.min_connection_count,
        max_size=settings.max_connection_count,
    )
    logger.info("Database connection pool created")
    return pool


async def close_db_pool(pool: asyncpg.Pool) -> None:
    """
    Close the database connection pool.

    Args:
        pool: asyncpg connection pool to close
    """
    logger.info("Closing database connection pool")
    await pool.close()
    logger.info("Database connection pool closed")


def get_db_pool_from_app(app: FastAPI) -> asyncpg.Pool:
    """
    Get the shared database pool from FastAPI app state.

    Args:
        app: FastAPI application instance

    Returns:
        asyncpg connection pool

    Raises:
        AttributeError: If pool is not initialized in app.state
    """
    if not hasattr(app.state, "db_pool"):
        raise AttributeError("Database pool not initialized. Call connect_to_db first.")
    return app.state.db_pool

