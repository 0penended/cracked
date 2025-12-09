import logging
import sys
from typing import Any, Dict, List, Tuple

from loguru import logger
from pydantic import PostgresDsn

from wallet_tracker.core.logging import InterceptHandler
from wallet_tracker.core.settings.base import BaseAppSettings


class AppSettings(BaseAppSettings):
    debug: bool = False
    docs_url: str = "/docs"
    openapi_prefix: str = ""
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = "FastAPI example application"
    version: str = "0.0.0"

    database_url: PostgresDsn
    max_connection_count: int = 10
    min_connection_count: int = 10

    api_prefix: str = "/api"

    allowed_hosts: List[str] = ["*"]

    logging_level: int = logging.INFO
    loggers: Tuple[str, str] = ("uvicorn.asgi", "uvicorn.access")
    coinmarketcap_api_key: str
    coinmarketcap_base_url: str
    
    # Hyperliquid API URL
    hyperliquid_api_url: str = "https://api.hyperliquid-testnet.xyz"

    # Telegram configuration
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # BigQuery configuration for token price sync
    bigquery_positions_dataset: str = "your_dataset"
    bigquery_positions_table: str = "positions"
    bigquery_prices_dataset: str = "your_dataset"
    bigquery_prices_table: str = "coin_prices"
    
    # Transaction processing configuration
    min_transaction_value: float = 1

    class Config:
        validate_assignment = True

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        return {
            "debug": self.debug,
            "docs_url": self.docs_url,
            "openapi_prefix": self.openapi_prefix,
            "openapi_url": self.openapi_url,
            "redoc_url": self.redoc_url,
            "title": self.title,
            "version": self.version,
        }

    def configure_logging(self) -> None:
        logging.getLogger().handlers = [InterceptHandler()]
        for logger_name in self.loggers:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = [InterceptHandler(level=self.logging_level)]

        logger.configure(handlers=[{"sink": sys.stderr, "level": self.logging_level}])
