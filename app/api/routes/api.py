from fastapi import APIRouter

from app.api.routes import articles, authentication, comments, profiles, tags, users

api_router = APIRouter()
api_router.include_router(authentication.router, tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(comments.router, prefix="/articles", tags=["comments"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])


@api_router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring."""
    from app.clients.cache import token_cache

    return token_cache.get_stats()
