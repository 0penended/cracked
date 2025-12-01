from fastapi import APIRouter, Request

from wallet_tracker.api.routes import cache, sync, monitor

api_router = APIRouter()
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(monitor.router, prefix="/monitor", tags=["monitor"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
