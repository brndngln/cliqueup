"""
Social module - Repository for posts, stories, and interactions.
"""
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta

from ...core.database import Collections
from ...core.config import settings


class PostRepository:
    """Repository for post data operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.POSTS]
    
    async def find_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Find post by ID."""
        return await self.collection.find_one({"id": post_id}, {"_id": 0})
    
    async def create(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new post."""
        await self.collection.insert_one(post_data)
        return {k: v for k, v in post_data.items() if k != "_id"}
    
    async def delete(self, post_id: str, user_id: str) -> bool:
        """Delete a post (only by owner)."""
        result = await self.collection.delete_one({
            "id": post_id,
            "user_id": user_id
        })
        return result.deleted_count > 0
    
    async def increment_count(self, post_id: str, field: str, delta: int = 1) -> bool:
        """Increment a counter field."""
        result = await self.collection.update_one(
            {"id": post_id},
            {"$inc": {field: delta}}
        )
        return result.modified_count > 0
    
    async def get_feed(
        self, 
        user_ids: List[str], 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get feed posts from followed users."""
        cursor = self.collection.find(
            {"user_id": {"$in": user_ids}},
            {"_id": 0}
        ).sort("created_at", -1).skip(offset).limit(limit)
        return await cursor.to_list(limit)
    
    async def get_explore(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get trending/explore posts."""
        cursor = self.collection.find(
            {},
            {"_id": 0}
        ).sort("reactions_count", -1).skip(offset).limit(limit)
        return await cursor.to_list(limit)
    
    async def get_user_posts(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get posts by a user."""
        cursor = self.collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).skip(offset).limit(limit)
        return await cursor.to_list(limit)
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search posts by content or tags."""
        cursor = self.collection.find(
            {
                "$or": [
                    {"content": {"$regex": query, "$options": "i"}},
                    {"tags": {"$regex": query, "$options": "i"}}
                ]
            },
            {"_id": 0}
        ).sort("reactions_count", -1).limit(limit)
        return await cursor.to_list(limit)


class ReactionRepository:
    """Repository for post reactions."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.POST_REACTIONS]
    
    async def find_user_reaction(self, post_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user's reaction on a post."""
        return await self.collection.find_one({
            "post_id": post_id,
            "user_id": user_id
        }, {"_id": 0})
    
    async def create(self, reaction_data: Dict[str, Any]) -> bool:
        """Create a reaction."""
        await self.collection.insert_one(reaction_data)
        return True
    
    async def update(self, reaction_id: str, reaction_type: str, updated_at: str) -> bool:
        """Update a reaction."""
        result = await self.collection.update_one(
            {"id": reaction_id},
            {"$set": {"reaction_type": reaction_type, "updated_at": updated_at}}
        )
        return result.modified_count > 0
    
    async def delete(self, reaction_id: str) -> bool:
        """Delete a reaction."""
        result = await self.collection.delete_one({"id": reaction_id})
        return result.deleted_count > 0


class CommentRepository:
    """Repository for post comments."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.POST_COMMENTS]
    
    async def find_by_id(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """Find comment by ID."""
        return await self.collection.find_one({"id": comment_id}, {"_id": 0})
    
    async def create(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comment."""
        await self.collection.insert_one(comment_data)
        return {k: v for k, v in comment_data.items() if k != "_id"}
    
    async def get_post_comments(
        self, 
        post_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get comments on a post."""
        cursor = self.collection.find(
            {"post_id": post_id, "parent_id": None},
            {"_id": 0}
        ).sort("created_at", 1).skip(offset).limit(limit)
        return await cursor.to_list(limit)
    
    async def get_replies(
        self, 
        parent_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get replies to a comment."""
        cursor = self.collection.find(
            {"parent_id": parent_id},
            {"_id": 0}
        ).sort("created_at", 1).limit(limit)
        return await cursor.to_list(limit)
    
    async def increment_replies(self, comment_id: str, delta: int = 1) -> bool:
        """Increment replies count."""
        result = await self.collection.update_one(
            {"id": comment_id},
            {"$inc": {"replies_count": delta}}
        )
        return result.modified_count > 0


class StoryRepository:
    """Repository for stories."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.STORIES]
        self.views_collection = db[Collections.STORY_VIEWS]
    
    async def find_by_id(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Find story by ID."""
        return await self.collection.find_one({"id": story_id}, {"_id": 0})
    
    async def create(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a story."""
        await self.collection.insert_one(story_data)
        return {k: v for k, v in story_data.items() if k != "_id"}
    
    async def get_active_stories(
        self, 
        user_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Get active (non-expired) stories from users."""
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.collection.find(
            {
                "user_id": {"$in": user_ids},
                "expires_at": {"$gt": now}
            },
            {"_id": 0}
        ).sort([("user_id", 1), ("created_at", 1)])
        return await cursor.to_list(1000)
    
    async def get_user_stories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's active stories."""
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.collection.find(
            {
                "user_id": user_id,
                "expires_at": {"$gt": now}
            },
            {"_id": 0}
        ).sort("created_at", 1)
        return await cursor.to_list(100)
    
    async def record_view(self, story_id: str, viewer_id: str, timestamp: str) -> bool:
        """Record a story view."""
        existing = await self.views_collection.find_one({
            "story_id": story_id,
            "viewer_id": viewer_id
        })
        
        if existing:
            return False  # Already viewed
        
        await self.views_collection.insert_one({
            "story_id": story_id,
            "viewer_id": viewer_id,
            "viewed_at": timestamp
        })
        
        # Increment views count
        await self.collection.update_one(
            {"id": story_id},
            {"$inc": {"views_count": 1}}
        )
        
        return True
    
    async def has_viewed(self, story_id: str, viewer_id: str) -> bool:
        """Check if user has viewed a story."""
        return await self.views_collection.count_documents({
            "story_id": story_id,
            "viewer_id": viewer_id
        }) > 0
    
    async def get_viewers(self, story_id: str) -> List[str]:
        """Get list of viewer IDs."""
        cursor = self.views_collection.find(
            {"story_id": story_id},
            {"_id": 0, "viewer_id": 1}
        )
        views = await cursor.to_list(1000)
        return [v["viewer_id"] for v in views]
