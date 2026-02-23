"""
Profiles module - Pydantic schemas for profile operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""
    handle: Optional[str] = Field(None, min_length=3, max_length=30)
    display_name: Optional[str] = Field(None, min_length=1, max_length=50)
    bio: Optional[str] = Field(None, max_length=280)
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    is_private: Optional[bool] = None
    dating_link_mode: Optional[str] = None
    pronouns: Optional[str] = None
    interests: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    """Profile data response."""
    user_id: str
    handle: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    is_private: bool = False
    dating_link_mode: str = "curated"
    pronouns: Optional[str] = None
    interests: List[str] = []
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_following: bool = False
    is_followed_by: bool = False
    
    class Config:
        from_attributes = True


class FollowResponse(BaseModel):
    """Follow action response."""
    ok: bool
    action: str  # "followed" or "unfollowed"
    followers_count: int
    following_count: int


class FollowerListResponse(BaseModel):
    """List of followers/following."""
    users: List[ProfileResponse]
    total: int
    has_more: bool
