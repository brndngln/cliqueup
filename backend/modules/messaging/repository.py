"""
Messaging module - Repository for conversations and messages.
"""
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import Collections


class ConversationRepository:
    """Repository for conversations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.CONVERSATIONS]
    
    async def find_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"id": conversation_id}, {"_id": 0})
    
    async def create(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.collection.insert_one(conversation_data)
        return {k: v for k, v in conversation_data.items() if k != "_id"}
    
    async def update_timestamp(self, conversation_id: str, timestamp: str) -> bool:
        result = await self.collection.update_one(
            {"id": conversation_id},
            {"$set": {"updated_at": timestamp}}
        )
        return result.modified_count > 0


class ConversationMemberRepository:
    """Repository for conversation members."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.CONVERSATION_MEMBERS]
    
    async def find_membership(
        self, 
        conversation_id: str, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({
            "conversation_id": conversation_id,
            "user_id": user_id
        }, {"_id": 0})
    
    async def get_user_conversations(self, user_id: str) -> List[str]:
        """Get conversation IDs for a user."""
        cursor = self.collection.find(
            {"user_id": user_id},
            {"_id": 0, "conversation_id": 1}
        )
        memberships = await cursor.to_list(1000)
        return [m["conversation_id"] for m in memberships]
    
    async def get_members(self, conversation_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find(
            {"conversation_id": conversation_id},
            {"_id": 0}
        )
        return await cursor.to_list(100)
    
    async def create(self, member_data: Dict[str, Any]) -> bool:
        await self.collection.insert_one(member_data)
        return True
    
    async def find_dm_between(self, user_a_id: str, user_b_id: str) -> Optional[str]:
        """Find existing DM conversation between two users."""
        # Get user A's conversations
        cursor_a = self.collection.find({"user_id": user_a_id}, {"_id": 0})
        user_a_convs = await cursor_a.to_list(1000)
        
        for conv in user_a_convs:
            # Check if user B is in this conversation
            member_b = await self.collection.find_one({
                "conversation_id": conv["conversation_id"],
                "user_id": user_b_id
            })
            if member_b:
                # Verify it's a DM (only 2 members)
                count = await self.collection.count_documents({
                    "conversation_id": conv["conversation_id"]
                })
                if count == 2:
                    # Check conversation type
                    from core.database import Collections
                    conv_doc = await self.db[Collections.CONVERSATIONS].find_one({
                        "id": conv["conversation_id"],
                        "type": "dm"
                    })
                    if conv_doc:
                        return conv["conversation_id"]
        
        return None


class MessageRepository:
    """Repository for messages."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.MESSAGES]
    
    async def find_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"id": message_id}, {"_id": 0})
    
    async def create(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.collection.insert_one(message_data)
        return {k: v for k, v in message_data.items() if k != "_id"}
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation, newest first."""
        query = {"conversation_id": conversation_id}
        if before:
            query["created_at"] = {"$lt": before}
        
        cursor = self.collection.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        messages = await cursor.to_list(limit)
        return list(reversed(messages))  # Return in chronological order
    
    async def get_last_message(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get the last message in a conversation."""
        return await self.collection.find_one(
            {"conversation_id": conversation_id},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
