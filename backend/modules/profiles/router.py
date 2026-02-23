"""
Profiles module - API router for profile endpoints.
"""
from fastapi import APIRouter, Depends, Query
from typing import List

from ...core.database import Database
from ...core.security import get_current_user
from .schemas import ProfileUpdateRequest, ProfileResponse, FollowResponse
from .service import ProfileService

router = APIRouter(prefix="/profiles", tags=["Profiles"])


def get_profile_service() -> ProfileService:
    """Dependency injection for ProfileService."""
    db = Database.get_db()
    return ProfileService(db)


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Get current user's profile."""
    return await service.get_profile(current_user["id"])


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Update current user's profile."""
    return await service.update_profile(current_user["id"], request)


@router.get("/handle/{handle}", response_model=ProfileResponse)
async def get_profile_by_handle(
    handle: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Get a user's profile by handle."""
    return await service.get_profile_by_handle(handle, current_user["id"])


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Get a user's profile by ID."""
    return await service.get_profile(user_id, current_user["id"])


@router.post("/{user_id}/follow", response_model=FollowResponse)
async def follow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Follow a user."""
    return await service.follow_user(current_user["id"], user_id)


@router.delete("/{user_id}/follow", response_model=FollowResponse)
async def unfollow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Unfollow a user."""
    return await service.unfollow_user(current_user["id"], user_id)


@router.get("/{user_id}/followers", response_model=List[ProfileResponse])
async def get_followers(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Get user's followers."""
    return await service.get_followers(user_id, limit, offset, current_user["id"])


@router.get("/{user_id}/following", response_model=List[ProfileResponse])
async def get_following(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """Get users that user is following."""
    return await service.get_following(user_id, limit, offset, current_user["id"])
