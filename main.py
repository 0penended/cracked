"""Main application entrypoint - unified FastAPI app for wallet_tracker and price_action."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from loguru import logger

from wallet_tracker.api.errors.http_error import http_error_handler
from wallet_tracker.api.errors.validation_error import http422_error_handler
from wallet_tracker.api.routes.api import api_router
from wallet_tracker.core.config import get_app_settings
from wallet_tracker.core.events import start_wallet_tracker_services, stop_wallet_tracker_services
from shared.db.connection import close_db_pool, create_db_pool


def get_application() -> FastAPI:
    """
    Create and configure the unified FastAPI application.
    
    This app includes:
    - wallet_tracker: Blockchain transaction monitoring and alerts
    - price_action: Trading signal generation (routes can be added here)
    """
    settings = get_app_settings()

    settings.configure_logging()

    application = FastAPI(**settings.fastapi_kwargs)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Startup: Connect to DB and start services
    @application.on_event("startup")
    async def startup_event() -> None:
        """Startup event: connect to database and start background services."""
        # Connect to database (shared pool for all packages)
        logger.info("Connecting to database...")
        db_pool = await create_db_pool(settings)
        application.state.db_pool = db_pool
        # Keep backward compatibility
        application.state.pool = db_pool
        logger.info("✅ Database connected")
        # Start wallet_tracker services (encapsulated)
        await start_wallet_tracker_services(application, settings, db_pool)

        # TODO: Start price_action services here if needed
        # await start_price_action_services(application, settings, db_pool)

    # Shutdown: Stop services and close DB
    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        """Shutdown event: stop services and close database connection."""
        # Stop wallet_tracker services (encapsulated)
        await stop_wallet_tracker_services(application)

        # TODO: Stop price_action services here if needed
        # await stop_price_action_services(application)

        # Close database connection (only in main.py)
        if hasattr(application.state, "db_pool"):
            await close_db_pool(application.state.db_pool)
            logger.info("✅ Database connection closed")

        logger.info("✅ Application shutdown complete")

    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(RequestValidationError, http422_error_handler)

    # Include wallet_tracker routes
    application.include_router(api_router, prefix=settings.api_prefix)
    
    # TODO: Add price_action routes here when needed
    # from price_action.api.routes import price_action_router
    # application.include_router(price_action_router, prefix=f"{settings.api_prefix}/price-action")

    return application


app = get_application()

