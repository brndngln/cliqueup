"""
Social module - API router for posts, stories, and interactions.
"""
from fastapi import APIRouter, Depends, Query
from typing import List

from ...core.database import Database
from ...core.security import get_current_user
from .schemas import (
    PostCreateRequest, PostResponse, ReactionRequest, ReactionResponse,
    CommentCreateRequest, CommentResponse,
    StoryCreateRequest, StoryResponse, StoryGroupResponse,
    SearchResponse
)
from .service import PostService, CommentService, StoryService
from .repository import PostRepository

router = APIRouter(tags=["Social"])


def get_post_service() -> PostService:
    db = Database.get_db()
    return PostService(db)


def get_comment_service() -> CommentService:
    db = Database.get_db()
    return CommentService(db)


def get_story_service() -> StoryService:
    db = Database.get_db()
    return StoryService(db)


# ==================== Posts ====================

@router.post("/posts", response_model=PostResponse, tags=["Posts"])
async def create_post(
    request: PostCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    """Create a new post."""
    return await service.create_post(current_user, request)


@router.get("/posts/feed", response_model=List[PostResponse], tags=["Posts"])
async def get_feed(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    """Get personalized feed from followed users."""
    return await service.get_feed(current_user["id"], limit, offset)


@router.get("/posts/explore", response_model=List[PostResponse], tags=["Posts"])
async def get_explore(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    """Get trending/explore posts."""
    return await service.get_explore(current_user["id"], limit, offset)


@router.get("/posts/user/{user_id}", response_model=List[PostResponse], tags=["Posts"])
async def get_user_posts(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    """Get posts by a specific user."""
    return await service.get_user_posts(user_id, current_user["id"], limit, offset)


@router.get("/posts/{post_id}", response_model=PostResponse, tags=["Posts"])
async def get_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    """Get a single post."""
    return await service.get_post(post_id, current_user["id"])


@router.post("/posts/{post_id}/react", response_model=ReactionResponse, tags=["Posts"])
async def react_to_post(
    post_id: str,
    request: ReactionRequest,
    current_user: dict = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    """React to a post (toggle on same reaction type)."""
    return await service.react_to_post(post_id, current_user, request)


# ==================== Comments ====================

@router.post("/posts/{post_id}/comments", response_model=CommentResponse, tags=["Comments"])
async def create_comment(
    post_id: str,
    request: CommentCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service)
):
    """Create a comment on a post."""
    return await service.create_comment(post_id, current_user, request)


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse], tags=["Comments"])
async def get_comments(
    post_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: CommentService = Depends(get_comment_service)
):
    """Get comments on a post."""
    return await service.get_comments(post_id, limit, offset)


# ==================== Stories ====================

@router.post("/stories", response_model=StoryResponse, tags=["Stories"])
async def create_story(
    request: StoryCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: StoryService = Depends(get_story_service)
):
    """Create a new story (expires in 24 hours)."""
    return await service.create_story(current_user, request)


@router.get("/stories/feed", response_model=List[StoryGroupResponse], tags=["Stories"])
async def get_stories_feed(
    current_user: dict = Depends(get_current_user),
    service: StoryService = Depends(get_story_service)
):
    """Get stories from followed users grouped by user."""
    return await service.get_stories_feed(current_user["id"])


@router.post("/stories/{story_id}/view", tags=["Stories"])
async def view_story(
    story_id: str,
    current_user: dict = Depends(get_current_user),
    service: StoryService = Depends(get_story_service)
):
    """Mark a story as viewed."""
    viewed = await service.view_story(story_id, current_user["id"])
    return {"ok": True, "new_view": viewed}


# ==================== Search ====================

@router.get("/search", response_model=SearchResponse, tags=["Search"])
async def search(
    q: str = Query(min_length=1, max_length=100),
    current_user: dict = Depends(get_current_user)
):
    """Search users and posts."""
    db = Database.get_db()
    
    # Search users
    from ...core.database import Collections
    users_cursor = db[Collections.USERS].find(
        {
            "$or": [
                {"handle": {"$regex": q, "$options": "i"}},
                {"display_name": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "password_hash": 0}
    ).limit(10)
    users = await users_cursor.to_list(10)
    
    # Search posts
    post_repo = PostRepository(db)
    posts = await post_repo.search(q, limit=20)
    
    post_service = PostService(db)
    enriched_posts = [
        await post_service._enrich_post(post, current_user["id"]) 
        for post in posts
    ]
    
    return SearchResponse(
        users=users,
        posts=enriched_posts,
        query=q
    )
