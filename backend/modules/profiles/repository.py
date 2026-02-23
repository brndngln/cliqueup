"""
Profiles module - Repository for profile data access.
"""
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import Collections


class ProfileRepository:
    """Repository for profile data operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.PROFILES]
    
    async def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find profile by user ID."""
        return await self.collection.find_one({"user_id": user_id}, {"_id": 0})
    
    async def find_by_handle(self, handle: str) -> Optional[Dict[str, Any]]:
        """Find profile by handle."""
        return await self.collection.find_one({"handle": handle.lower()}, {"_id": 0})
    
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update profile data."""
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def increment_count(self, user_id: str, field: str, delta: int = 1) -> bool:
        """Increment a counter field."""
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$inc": {field: delta}}
        )
        return result.modified_count > 0
    
    async def handle_exists(self, handle: str, exclude_user_id: str = None) -> bool:
        """Check if handle exists (optionally excluding a user)."""
        query = {"handle": handle.lower()}
        if exclude_user_id:
            query["user_id"] = {"$ne": exclude_user_id}
        return await self.collection.count_documents(query) > 0
    
    async def get_multiple_by_user_ids(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple profiles by user IDs."""
        cursor = self.collection.find(
            {"user_id": {"$in": user_ids}},
            {"_id": 0}
        )
        return await cursor.to_list(len(user_ids))


class FollowRepository:
    """Repository for follow relationship operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.FOLLOWS]
    
    async def find_follow(self, follower_id: str, following_id: str) -> Optional[Dict[str, Any]]:
        """Find a follow relationship."""
        return await self.collection.find_one({
            "follower_id": follower_id,
            "following_id": following_id
        }, {"_id": 0})
    
    async def create(self, follow_data: Dict[str, Any]) -> bool:
        """Create a follow relationship."""
        await self.collection.insert_one(follow_data)
        return True
    
    async def delete(self, follower_id: str, following_id: str) -> bool:
        """Delete a follow relationship."""
        result = await self.collection.delete_one({
            "follower_id": follower_id,
            "following_id": following_id
        })
        return result.deleted_count > 0
    
    async def get_followers(self, user_id: str, limit: int = 50, offset: int = 0) -> List[str]:
        """Get list of follower IDs."""
        cursor = self.collection.find(
            {"following_id": user_id},
            {"_id": 0, "follower_id": 1}
        ).skip(offset).limit(limit)
        follows = await cursor.to_list(limit)
        return [f["follower_id"] for f in follows]
    
    async def get_following(self, user_id: str, limit: int = 50, offset: int = 0) -> List[str]:
        """Get list of following IDs."""
        cursor = self.collection.find(
            {"follower_id": user_id},
            {"_id": 0, "following_id": 1}
        ).skip(offset).limit(limit)
        follows = await cursor.to_list(limit)
        return [f["following_id"] for f in follows]
    
    async def count_followers(self, user_id: str) -> int:
        """Count followers."""
        return await self.collection.count_documents({"following_id": user_id})
    
    async def count_following(self, user_id: str) -> int:
        """Count following."""
        return await self.collection.count_documents({"follower_id": user_id})
    
    async def is_following(self, follower_id: str, following_id: str) -> bool:
        """Check if user is following another user."""
        return await self.collection.count_documents({
            "follower_id": follower_id,
            "following_id": following_id
        }) > 0
