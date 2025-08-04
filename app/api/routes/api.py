from fastapi import APIRouter

from app.api.routes import (
    articles,
    authentication,
    comments,
    profiles,
    tags,
    users,
    cache,
    sync,
)

api_router = APIRouter()
api_router.include_router(authentication.router, tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(comments.router, prefix="/articles", tags=["comments"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])

# Cache management routes
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])

# Sync routes
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
