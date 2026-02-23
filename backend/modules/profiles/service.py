"""
Profiles module - Service layer for profile business logic.
"""
from typing import Optional, List
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.database import Collections
from ...core.enums import NotificationType
from ...utils.helpers import generate_id, utc_now_iso
from .repository import ProfileRepository, FollowRepository
from .schemas import ProfileUpdateRequest, ProfileResponse, FollowResponse


class ProfileService:
    """Service for profile operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.follow_repo = FollowRepository(db)
    
    async def get_profile(
        self, 
        user_id: str, 
        current_user_id: Optional[str] = None
    ) -> ProfileResponse:
        """Get a user's profile."""
        profile = await self.profile_repo.find_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Check follow status if viewer is logged in
        is_following = False
        is_followed_by = False
        if current_user_id and current_user_id != user_id:
            is_following = await self.follow_repo.is_following(current_user_id, user_id)
            is_followed_by = await self.follow_repo.is_following(user_id, current_user_id)
        
        return ProfileResponse(
            **profile,
            is_following=is_following,
            is_followed_by=is_followed_by
        )
    
    async def get_profile_by_handle(
        self, 
        handle: str,
        current_user_id: Optional[str] = None
    ) -> ProfileResponse:
        """Get a user's profile by handle."""
        profile = await self.profile_repo.find_by_handle(handle)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        is_following = False
        is_followed_by = False
        if current_user_id and current_user_id != profile["user_id"]:
            is_following = await self.follow_repo.is_following(current_user_id, profile["user_id"])
            is_followed_by = await self.follow_repo.is_following(profile["user_id"], current_user_id)
        
        return ProfileResponse(
            **profile,
            is_following=is_following,
            is_followed_by=is_followed_by
        )
    
    async def update_profile(
        self, 
        user_id: str, 
        request: ProfileUpdateRequest
    ) -> ProfileResponse:
        """Update a user's profile."""
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}
        
        if "handle" in update_data:
            handle = update_data["handle"].lower()
            if await self.profile_repo.handle_exists(handle, exclude_user_id=user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Handle already taken"
                )
            update_data["handle"] = handle
            
            # Also update user record
            await self.db[Collections.USERS].update_one(
                {"id": user_id},
                {"$set": {"handle": handle}}
            )
        
        if "display_name" in update_data:
            await self.db[Collections.USERS].update_one(
                {"id": user_id},
                {"$set": {"display_name": update_data["display_name"]}}
            )
        
        update_data["updated_at"] = utc_now_iso()
        
        await self.profile_repo.update(user_id, update_data)
        
        profile = await self.profile_repo.find_by_user_id(user_id)
        return ProfileResponse(**profile)
    
    async def follow_user(self, follower_id: str, following_id: str) -> FollowResponse:
        """Follow a user."""
        if follower_id == following_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot follow yourself"
            )
        
        # Check target exists
        target_profile = await self.profile_repo.find_by_user_id(following_id)
        if not target_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check not already following
        if await self.follow_repo.is_following(follower_id, following_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already following this user"
            )
        
        now = utc_now_iso()
        
        # Create follow relationship
        follow_data = {
            "id": generate_id(),
            "follower_id": follower_id,
            "following_id": following_id,
            "created_at": now,
        }
        await self.follow_repo.create(follow_data)
        
        # Update counts
        await self.profile_repo.increment_count(follower_id, "following_count", 1)
        await self.profile_repo.increment_count(following_id, "followers_count", 1)
        
        # Create notification
        follower_profile = await self.profile_repo.find_by_user_id(follower_id)
        notification = {
            "id": generate_id(),
            "user_id": following_id,
            "type": NotificationType.FOLLOW.value,
            "title": "New Follower",
            "body": f"{follower_profile['display_name']} started following you",
            "data": {"follower_id": follower_id},
            "read": False,
            "created_at": now,
        }
        await self.db[Collections.NOTIFICATIONS].insert_one(notification)
        
        # Get updated counts
        followers_count = await self.follow_repo.count_followers(following_id)
        following_count = await self.follow_repo.count_following(follower_id)
        
        return FollowResponse(
            ok=True,
            action="followed",
            followers_count=followers_count,
            following_count=following_count
        )
    
    async def unfollow_user(self, follower_id: str, following_id: str) -> FollowResponse:
        """Unfollow a user."""
        if not await self.follow_repo.delete(follower_id, following_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not following this user"
            )
        
        # Update counts
        await self.profile_repo.increment_count(follower_id, "following_count", -1)
        await self.profile_repo.increment_count(following_id, "followers_count", -1)
        
        followers_count = await self.follow_repo.count_followers(following_id)
        following_count = await self.follow_repo.count_following(follower_id)
        
        return FollowResponse(
            ok=True,
            action="unfollowed",
            followers_count=followers_count,
            following_count=following_count
        )
    
    async def get_followers(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        current_user_id: Optional[str] = None
    ) -> List[ProfileResponse]:
        """Get user's followers."""
        follower_ids = await self.follow_repo.get_followers(user_id, limit, offset)
        profiles = await self.profile_repo.get_multiple_by_user_ids(follower_ids)
        
        result = []
        for profile in profiles:
            is_following = False
            is_followed_by = False
            if current_user_id:
                is_following = await self.follow_repo.is_following(current_user_id, profile["user_id"])
                is_followed_by = await self.follow_repo.is_following(profile["user_id"], current_user_id)
            result.append(ProfileResponse(**profile, is_following=is_following, is_followed_by=is_followed_by))
        
        return result
    
    async def get_following(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        current_user_id: Optional[str] = None
    ) -> List[ProfileResponse]:
        """Get users that user is following."""
        following_ids = await self.follow_repo.get_following(user_id, limit, offset)
        profiles = await self.profile_repo.get_multiple_by_user_ids(following_ids)
        
        result = []
        for profile in profiles:
            is_following = False
            is_followed_by = False
            if current_user_id:
                is_following = await self.follow_repo.is_following(current_user_id, profile["user_id"])
                is_followed_by = await self.follow_repo.is_following(profile["user_id"], current_user_id)
            result.append(ProfileResponse(**profile, is_following=is_following, is_followed_by=is_followed_by))
        
        return result
