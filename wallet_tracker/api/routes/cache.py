from fastapi import APIRouter, Depends
from loguru import logger

from wallet_tracker.clients.cache import token_cache

router = APIRouter()


@router.get("/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring."""
    return token_cache.get_stats()


@router.post("/cleanup")
async def cleanup_cache():
    """Clean up expired cache entries. Designed to be called by external cron jobs."""
    try:
        # Clean up expired entries
        await token_cache.cleanup_expired()

        # Get stats after cleanup
        stats = token_cache.get_stats()

        logger.info(f"Cache cleanup completed: {stats}")

        return {"success": True, "message": "Cache cleanup completed", "stats": stats}

    except Exception as e:
        logger.error(f"Error during cache cleanup: {e}")
        return {
            "success": False,
            "message": f"Cache cleanup failed: {str(e)}",
            "stats": token_cache.get_stats(),
        }
