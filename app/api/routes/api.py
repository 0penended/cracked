from fastapi import APIRouter, Request

from app.api.routes import cache, sync

api_router = APIRouter()
# Cache management routes
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
# Sync routes
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@api_router.get("/blockchain-monitor/status")
async def blockchain_monitor_status(request: Request):
    """Get the status of the blockchain monitoring service."""
    if hasattr(request.app.state, "blockchain_service"):
        service = request.app.state.blockchain_service
        return {
            "status": "running" if service.is_running else "stopped",
            "is_running": service.is_running,
        }
    else:
        return {"status": "not_initialized", "is_running": False}
