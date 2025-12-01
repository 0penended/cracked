from fastapi import FastAPI
from loguru import logger

from shared.db.connection import close_db_pool, create_db_pool
from wallet_tracker.core.settings.app import AppSettings


async def connect_to_db(app: FastAPI, settings: AppSettings) -> None:
    """Connect to database and store pool in app.state."""
    pool = await create_db_pool(settings)
    app.state.db_pool = pool
    # Keep backward compatibility
    app.state.pool = pool


async def close_db_connection(app: FastAPI) -> None:
    """Close database connection pool."""
    if hasattr(app.state, "db_pool"):
        await close_db_pool(app.state.db_pool)
        del app.state.db_pool
    if hasattr(app.state, "pool"):
        del app.state.pool
