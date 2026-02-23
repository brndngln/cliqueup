"""
Database connection and collection management.
Provides async MongoDB connection with Motor.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """Singleton database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    def connect(cls) -> AsyncIOMotorDatabase:
        """Initialize database connection."""
        if cls.client is None:
            cls.client = AsyncIOMotorClient(settings.MONGO_URL)
            cls.db = cls.client[settings.DB_NAME]
            logger.info(f"Connected to MongoDB: {settings.DB_NAME}")
        return cls.db
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.db is None:
            return cls.connect()
        return cls.db
    
    @classmethod
    async def close(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Closed MongoDB connection")


# Collection names - centralized for consistency
class Collections:
    """Database collection names."""
    USERS = "users"
    PROFILES = "profiles"
    ENTITLEMENTS = "entitlements"
    MEET_ACCESS = "meet_access"
    DATING_PROFILES = "dating_profiles"
    SQUADS = "squads"
    SQUAD_MEMBERS = "squad_members"
    SQUAD_INVITES = "squad_invites"
    SQUAD_SWIPES = "squad_swipes"
    SQUAD_SWIPE_VOTES = "squad_swipe_votes"
    SQUAD_MATCHES = "squad_matches"
    FOLLOWS = "follows"
    POSTS = "posts"
    POST_REACTIONS = "post_reactions"
    POST_COMMENTS = "post_comments"
    STORIES = "stories"
    STORY_VIEWS = "story_views"
    CONVERSATIONS = "conversations"
    CONVERSATION_MEMBERS = "conversation_members"
    MESSAGES = "messages"
    NOTIFICATIONS = "notifications"


def get_db() -> AsyncIOMotorDatabase:
    """Dependency injection helper for database."""
    return Database.get_db()
