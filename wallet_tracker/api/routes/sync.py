from fastapi import APIRouter, Depends
from loguru import logger

from wallet_tracker.services.price_sync import TokenPriceSyncService
from wallet_tracker.api.dependencies.services import get_token_price_sync_service

router = APIRouter()


@router.post("/token-prices")
async def sync_token_prices(
    service: TokenPriceSyncService = Depends(get_token_price_sync_service),
):
    """Sync token prices from DexScreener and CoinMarketCap to BigQuery. Designed to be called by external cron jobs."""
    try:
        result = await service.sync_all_token_prices()

        logger.info(f"Token price sync completed: {result}")

        return {
            "success": True,
            "message": "Token price sync completed",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error during token price sync: {e}")
        return {"success": False, "message": f"Token price sync failed: {str(e)}"}
