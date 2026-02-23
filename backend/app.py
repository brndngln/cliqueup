"""
CliqUp Backend - Elite Modular Architecture
============================================

A social + dating platform with squad-first group matching.

Architecture:
- Modular domain-driven design
- Repository pattern for data access
- Service layer for business logic
- Elo-based matching algorithm

Modules:
- Identity: Authentication and user management
- Profiles: User profiles and follow system
- Social: Posts, stories, reactions, comments
- Meet: Dating features with squad matching
- Messaging: Conversations and messages
"""
from fastapi import FastAPI, APIRouter, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import logging

from core.config import settings
from core.database import Database, Collections
from core.security import get_current_user
from utils.helpers import generate_id, utc_now_iso

# Import routers
from modules.identity import router as identity_router
from modules.profiles import router as profiles_router
from modules.social import router as social_router
from modules.meet import router as meet_router
from modules.messaging import router as messaging_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    Database.connect()
    
    # Create indexes
    db = Database.get_db()
    try:
        await db[Collections.USERS].create_index("email", unique=True, sparse=True)
        await db[Collections.USERS].create_index("phone_e164", unique=True, sparse=True)
        await db[Collections.USERS].create_index("handle", unique=True)
        await db[Collections.PROFILES].create_index("user_id", unique=True)
        await db[Collections.PROFILES].create_index("handle", unique=True)
        await db[Collections.FOLLOWS].create_index([("follower_id", 1), ("following_id", 1)], unique=True)
        await db[Collections.POSTS].create_index([("user_id", 1), ("created_at", -1)])
        await db[Collections.POSTS].create_index([("created_at", -1)])
        await db[Collections.SQUAD_MEMBERS].create_index([("squad_id", 1), ("user_id", 1)], unique=True)
        await db[Collections.MESSAGES].create_index([("conversation_id", 1), ("created_at", -1)])
        logger.info("Database indexes created")
    except Exception as e:
        logger.warning(f"Index creation (may already exist): {e}")
    
    yield
    
    # Shutdown
    await Database.close()
    logger.info(f"{settings.APP_NAME} shutdown complete")


# Create application
app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Social + Dating Platform with Squad-First Matching",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
api_router = APIRouter(prefix="/api")

# Include module routers
api_router.include_router(identity_router)
api_router.include_router(profiles_router)
api_router.include_router(social_router)
api_router.include_router(meet_router)
api_router.include_router(messaging_router)


# ==================== Notifications (inline for simplicity) ====================

from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    body: str
    data: dict = {}
    read: bool = False
    created_at: str


@api_router.get("/notifications", response_model=List[NotificationResponse], tags=["Notifications"])
async def get_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    unread_only: bool = Query(default=False),
    current_user: dict = Depends(get_current_user)
):
    """Get user's notifications."""
    db = Database.get_db()
    query = {"user_id": current_user["id"]}
    if unread_only:
        query["read"] = False
    
    cursor = db[Collections.NOTIFICATIONS].find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit)
    
    notifications = await cursor.to_list(limit)
    return [NotificationResponse(**n) for n in notifications]


@api_router.get("/notifications/unread-count", tags=["Notifications"])
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications."""
    db = Database.get_db()
    count = await db[Collections.NOTIFICATIONS].count_documents({
        "user_id": current_user["id"],
        "read": False
    })
    return {"unread_count": count}


@api_router.post("/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read."""
    db = Database.get_db()
    result = await db[Collections.NOTIFICATIONS].update_one(
        {"id": notification_id, "user_id": current_user["id"]},
        {"$set": {"read": True}}
    )
    return {"ok": result.modified_count > 0}


@api_router.post("/notifications/read-all", tags=["Notifications"])
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read."""
    db = Database.get_db()
    result = await db[Collections.NOTIFICATIONS].update_many(
        {"user_id": current_user["id"], "read": False},
        {"$set": {"read": True}}
    )
    return {"ok": True, "marked_count": result.modified_count}


# ==================== Health Check ====================

@api_router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Include API router
app.include_router(api_router)


# Root redirect
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
