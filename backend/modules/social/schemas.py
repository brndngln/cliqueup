"""
Social module - Pydantic schemas for posts, stories, and interactions.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ==================== Post Schemas ====================

class PostCreateRequest(BaseModel):
    """Create post request."""
    type: str = "text"  # text, photo, video, carousel
    content: str = Field(max_length=5000)
    media_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class PostResponse(BaseModel):
    """Post response with engagement data."""
    id: str
    user_id: str
    user_name: str
    user_handle: str
    user_avatar: Optional[str] = None
    type: str
    content: str
    media_urls: List[str] = []
    tags: List[str] = []
    reactions_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    user_reaction: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class ReactionRequest(BaseModel):
    """React to post request."""
    reaction_type: str = "like"  # like, love, laugh, wow, sad, angry


class ReactionResponse(BaseModel):
    """Reaction action response."""
    ok: bool
    action: str  # "added", "removed", "updated"
    reaction_type: Optional[str] = None
    reactions_count: int


# ==================== Comment Schemas ====================

class CommentCreateRequest(BaseModel):
    """Create comment request."""
    content: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[str] = None  # For replies


class CommentResponse(BaseModel):
    """Comment response."""
    id: str
    post_id: str
    user_id: str
    user_name: str
    user_handle: str
    user_avatar: Optional[str] = None
    content: str
    parent_id: Optional[str] = None
    replies_count: int = 0
    created_at: str
    
    class Config:
        from_attributes = True


# ==================== Story Schemas ====================

class StoryCreateRequest(BaseModel):
    """Create story request."""
    media_url: str
    media_type: str = "image"  # image, video
    caption: Optional[str] = Field(None, max_length=200)
    duration: int = Field(default=5, ge=3, le=30)  # seconds


class StoryResponse(BaseModel):
    """Story response."""
    id: str
    user_id: str
    user_name: str
    user_handle: str
    user_avatar: Optional[str] = None
    media_url: str
    media_type: str
    caption: Optional[str] = None
    duration: int
    views_count: int = 0
    has_viewed: bool = False
    created_at: str
    expires_at: str
    
    class Config:
        from_attributes = True


class StoryGroupResponse(BaseModel):
    """Stories grouped by user."""
    user_id: str
    user_name: str
    user_handle: str
    user_avatar: Optional[str] = None
    stories: List[StoryResponse]
    has_unseen: bool = False


# ==================== Search Schemas ====================

class SearchResponse(BaseModel):
    """Search results response."""
    users: List[dict] = []
    posts: List[PostResponse] = []
    query: str
