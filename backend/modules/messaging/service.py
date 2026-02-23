"""
Messaging module - Service layer for conversations and messages.
"""
from typing import Optional, List
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.database import Collections
from ...core.enums import ConversationType, NotificationType
from ...utils.helpers import generate_id, utc_now_iso
from .repository import ConversationRepository, ConversationMemberRepository, MessageRepository
from .schemas import (
    ConversationResponse, ConversationMemberResponse, MessageResponse,
    MessageCreateRequest, ConversationCreateRequest
)


class MessagingService:
    """Service for messaging operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.member_repo = ConversationMemberRepository(db)
        self.msg_repo = MessageRepository(db)
    
    async def get_conversations(self, user_id: str) -> List[ConversationResponse]:
        """Get all conversations for a user."""
        conv_ids = await self.member_repo.get_user_conversations(user_id)
        
        if not conv_ids:
            return []
        
        result = []
        for conv_id in conv_ids:
            conv = await self.conv_repo.find_by_id(conv_id)
            if conv:
                members = await self._get_members(conv_id)
                last_message = await self._get_last_message(conv_id)
                
                result.append(ConversationResponse(
                    id=conv["id"],
                    type=conv["type"],
                    name=conv.get("name"),
                    created_by=conv["created_by"],
                    members=members,
                    last_message=last_message,
                    unread_count=0,  # TODO: Implement read tracking
                    created_at=conv["created_at"],
                    updated_at=conv.get("updated_at", conv["created_at"])
                ))
        
        # Sort by updated_at descending
        result.sort(key=lambda x: x.updated_at, reverse=True)
        return result
    
    async def get_conversation(self, conversation_id: str, user_id: str) -> ConversationResponse:
        """Get a single conversation."""
        # Verify membership
        membership = await self.member_repo.find_membership(conversation_id, user_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this conversation"
            )
        
        conv = await self.conv_repo.find_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        members = await self._get_members(conversation_id)
        last_message = await self._get_last_message(conversation_id)
        
        return ConversationResponse(
            id=conv["id"],
            type=conv["type"],
            name=conv.get("name"),
            created_by=conv["created_by"],
            members=members,
            last_message=last_message,
            unread_count=0,
            created_at=conv["created_at"],
            updated_at=conv.get("updated_at", conv["created_at"])
        )
    
    async def get_messages(
        self, 
        conversation_id: str, 
        user_id: str,
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[MessageResponse]:
        """Get messages from a conversation."""
        # Verify membership
        membership = await self.member_repo.find_membership(conversation_id, user_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this conversation"
            )
        
        messages = await self.msg_repo.get_conversation_messages(conversation_id, limit, before)
        
        result = []
        for msg in messages:
            user = await self.db[Collections.USERS].find_one(
                {"id": msg["sender_id"]}, {"_id": 0}
            )
            profile = await self.db[Collections.PROFILES].find_one(
                {"user_id": msg["sender_id"]}, {"_id": 0}
            )
            
            result.append(MessageResponse(
                id=msg["id"],
                conversation_id=msg["conversation_id"],
                sender_id=msg["sender_id"],
                sender_name=user.get("display_name", "Unknown") if user else "Unknown",
                sender_avatar=profile.get("avatar_url") if profile else None,
                body=msg["body"],
                created_at=msg["created_at"]
            ))
        
        return result
    
    async def send_message(
        self, 
        conversation_id: str, 
        user: dict, 
        request: MessageCreateRequest
    ) -> MessageResponse:
        """Send a message to a conversation."""
        # Verify membership
        membership = await self.member_repo.find_membership(conversation_id, user["id"])
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this conversation"
            )
        
        now = utc_now_iso()
        msg_id = generate_id()
        
        message_data = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "sender_id": user["id"],
            "body": request.body,
            "created_at": now,
        }
        
        await self.msg_repo.create(message_data)
        
        # Update conversation timestamp
        await self.conv_repo.update_timestamp(conversation_id, now)
        
        # Create notifications for other members
        members = await self.member_repo.get_members(conversation_id)
        for m in members:
            if m["user_id"] != user["id"]:
                notification = {
                    "id": generate_id(),
                    "user_id": m["user_id"],
                    "type": NotificationType.MESSAGE.value,
                    "title": "New Message",
                    "body": f"{user['display_name']}: {request.body[:50]}...",
                    "data": {"conversation_id": conversation_id, "message_id": msg_id},
                    "read": False,
                    "created_at": now,
                }
                await self.db[Collections.NOTIFICATIONS].insert_one(notification)
        
        profile = await self.db[Collections.PROFILES].find_one(
            {"user_id": user["id"]}, {"_id": 0}
        )
        
        return MessageResponse(
            id=msg_id,
            conversation_id=conversation_id,
            sender_id=user["id"],
            sender_name=user["display_name"],
            sender_avatar=profile.get("avatar_url") if profile else None,
            body=request.body,
            created_at=now
        )
    
    async def create_dm(self, user: dict, target_user_id: str) -> ConversationResponse:
        """Create or get existing DM conversation."""
        if user["id"] == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create DM with yourself"
            )
        
        # Check target exists
        target = await self.db[Collections.USERS].find_one({"id": target_user_id})
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check for existing DM
        existing_conv_id = await self.member_repo.find_dm_between(user["id"], target_user_id)
        if existing_conv_id:
            return await self.get_conversation(existing_conv_id, user["id"])
        
        # Create new DM
        now = utc_now_iso()
        conv_id = generate_id()
        
        conversation = {
            "id": conv_id,
            "type": ConversationType.DM.value,
            "name": None,
            "created_by": user["id"],
            "created_at": now,
            "updated_at": now,
        }
        await self.conv_repo.create(conversation)
        
        # Add both members
        for uid in [user["id"], target_user_id]:
            await self.member_repo.create({
                "id": generate_id(),
                "conversation_id": conv_id,
                "user_id": uid,
                "joined_at": now,
            })
        
        members = await self._get_members(conv_id)
        
        return ConversationResponse(
            id=conv_id,
            type=ConversationType.DM.value,
            name=None,
            created_by=user["id"],
            members=members,
            last_message=None,
            unread_count=0,
            created_at=now,
            updated_at=now
        )
    
    async def create_group(
        self, 
        user: dict, 
        request: ConversationCreateRequest
    ) -> ConversationResponse:
        """Create a group conversation."""
        now = utc_now_iso()
        conv_id = generate_id()
        
        conversation = {
            "id": conv_id,
            "type": ConversationType.GROUP.value,
            "name": request.name,
            "created_by": user["id"],
            "created_at": now,
            "updated_at": now,
        }
        await self.conv_repo.create(conversation)
        
        # Add creator and all members
        all_members = list(set([user["id"]] + request.member_ids))
        for uid in all_members:
            await self.member_repo.create({
                "id": generate_id(),
                "conversation_id": conv_id,
                "user_id": uid,
                "joined_at": now,
            })
        
        members = await self._get_members(conv_id)
        
        return ConversationResponse(
            id=conv_id,
            type=ConversationType.GROUP.value,
            name=request.name,
            created_by=user["id"],
            members=members,
            last_message=None,
            unread_count=0,
            created_at=now,
            updated_at=now
        )
    
    async def _get_members(self, conversation_id: str) -> List[ConversationMemberResponse]:
        """Get conversation members with user info."""
        members = await self.member_repo.get_members(conversation_id)
        result = []
        
        for m in members:
            user = await self.db[Collections.USERS].find_one(
                {"id": m["user_id"]}, {"_id": 0}
            )
            profile = await self.db[Collections.PROFILES].find_one(
                {"user_id": m["user_id"]}, {"_id": 0}
            )
            
            if user:
                result.append(ConversationMemberResponse(
                    user_id=m["user_id"],
                    display_name=user.get("display_name", "Unknown"),
                    avatar_url=profile.get("avatar_url") if profile else None
                ))
        
        return result
    
    async def _get_last_message(self, conversation_id: str) -> Optional[MessageResponse]:
        """Get last message in conversation."""
        msg = await self.msg_repo.get_last_message(conversation_id)
        if not msg:
            return None
        
        user = await self.db[Collections.USERS].find_one(
            {"id": msg["sender_id"]}, {"_id": 0}
        )
        profile = await self.db[Collections.PROFILES].find_one(
            {"user_id": msg["sender_id"]}, {"_id": 0}
        )
        
        return MessageResponse(
            id=msg["id"],
            conversation_id=msg["conversation_id"],
            sender_id=msg["sender_id"],
            sender_name=user.get("display_name", "Unknown") if user else "Unknown",
            sender_avatar=profile.get("avatar_url") if profile else None,
            body=msg["body"],
            created_at=msg["created_at"]
        )
