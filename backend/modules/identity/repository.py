"""
Identity module - Repository for user data access.
"""
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import Collections


class UserRepository:
    """Repository for user data operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.USERS]
    
    async def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID."""
        return await self.collection.find_one({"id": user_id}, {"_id": 0})
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email."""
        return await self.collection.find_one({"email": email}, {"_id": 0})
    
    async def find_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Find user by phone number."""
        return await self.collection.find_one({"phone_e164": phone}, {"_id": 0})
    
    async def find_by_handle(self, handle: str) -> Optional[Dict[str, Any]]:
        """Find user by handle."""
        return await self.collection.find_one({"handle": handle.lower()}, {"_id": 0})
    
    async def find_by_email_or_phone(
        self, 
        email: Optional[str] = None, 
        phone: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find user by email or phone."""
        query = {}
        if email:
            query["email"] = email
        if phone:
            query["phone_e164"] = phone
        
        if not query:
            return None
        
        return await self.collection.find_one(query, {"_id": 0})
    
    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        await self.collection.insert_one(user_data)
        return {k: v for k, v in user_data.items() if k != "_id"}
    
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data."""
        result = await self.collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        return await self.collection.count_documents({"email": email}) > 0
    
    async def exists_by_phone(self, phone: str) -> bool:
        """Check if user exists by phone."""
        return await self.collection.count_documents({"phone_e164": phone}) > 0
    
    async def exists_by_handle(self, handle: str) -> bool:
        """Check if user exists by handle."""
        return await self.collection.count_documents({"handle": handle.lower()}) > 0
    
    async def search_users(
        self, 
        query: str, 
        limit: int = 20,
        exclude_ids: list = None
    ) -> list:
        """Search users by handle or display name."""
        exclude_ids = exclude_ids or []
        filter_query = {
            "$and": [
                {"id": {"$nin": exclude_ids}},
                {
                    "$or": [
                        {"handle": {"$regex": query, "$options": "i"}},
                        {"display_name": {"$regex": query, "$options": "i"}}
                    ]
                }
            ]
        }
        
        cursor = self.collection.find(filter_query, {"_id": 0, "password_hash": 0})
        return await cursor.limit(limit).to_list(limit)
