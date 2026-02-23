"""
Messaging module - API router for conversations and messages.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from ...core.database import Database
from ...core.security import get_current_user
from .schemas import (
    ConversationResponse, MessageResponse,
    MessageCreateRequest, ConversationCreateRequest
)
from .service import MessagingService

router = APIRouter(prefix="/conversations", tags=["Messaging"])


def get_messaging_service() -> MessagingService:
    return MessagingService(Database.get_db())


@router.get("", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: dict = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service)
):
    """Get all conversations for the current user."""
    return await service.get_conversations(current_user["id"])


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service)
):
    """Get a single conversation."""
    return await service.get_conversation(conversation_id, current_user["id"])


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    before: Optional[str] = Query(default=None, description="Load messages before this timestamp"),
    current_user: dict = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service)
):
    """Get messages from a conversation."""
    return await service.get_messages(conversation_id, current_user["id"], limit, before)


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: MessageCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service)
):
    """Send a message to a conversation."""
    return await service.send_message(conversation_id, current_user, request)


@router.post("/dm/{user_id}", response_model=ConversationResponse)
async def create_dm(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service)
):
    """Create or get existing DM conversation with a user."""
    return await service.create_dm(current_user, user_id)


@router.post("/group", response_model=ConversationResponse)
async def create_group(
    request: ConversationCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service)
):
    """Create a group conversation."""
    return await service.create_group(current_user, request)
