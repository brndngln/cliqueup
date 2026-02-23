"""
Messaging module - Pydantic schemas for conversations and messages.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ConversationMemberResponse(BaseModel):
    """Conversation member info."""
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None


class MessageResponse(BaseModel):
    """Message response."""
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    sender_avatar: Optional[str] = None
    body: str
    created_at: str
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: str
    type: str  # dm, group, meet_group
    name: Optional[str] = None
    created_by: str
    members: List[ConversationMemberResponse] = []
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class MessageCreateRequest(BaseModel):
    """Create message request."""
    body: str = Field(min_length=1, max_length=4000)


class ConversationCreateRequest(BaseModel):
    """Create group conversation request."""
    name: Optional[str] = Field(None, max_length=100)
    member_ids: List[str] = Field(min_length=1, max_length=50)
