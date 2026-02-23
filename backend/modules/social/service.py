"""
Social module - Service layer for posts, stories, and interactions.
"""
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.database import Collections
from ...core.config import settings
from ...core.enums import NotificationType
from ...utils.helpers import generate_id, utc_now_iso
from .repository import PostRepository, ReactionRepository, CommentRepository, StoryRepository
from .schemas import (
    PostCreateRequest, PostResponse, ReactionRequest, ReactionResponse,
    CommentCreateRequest, CommentResponse,
    StoryCreateRequest, StoryResponse, StoryGroupResponse
)


class PostService:
    """Service for post operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.post_repo = PostRepository(db)
        self.reaction_repo = ReactionRepository(db)
        self.comment_repo = CommentRepository(db)
    
    async def create_post(self, user: dict, request: PostCreateRequest) -> PostResponse:
        """Create a new post."""
        now = utc_now_iso()
        post_id = generate_id()
        
        post_data = {
            "id": post_id,
            "user_id": user["id"],
            "type": request.type,
            "content": request.content,
            "media_urls": request.media_urls or [],
            "tags": request.tags or [],
            "reactions_count": 0,
            "comments_count": 0,
            "shares_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        
        await self.post_repo.create(post_data)
        
        # Update user's posts count
        await self.db[Collections.PROFILES].update_one(
            {"user_id": user["id"]},
            {"$inc": {"posts_count": 1}}
        )
        
        profile = await self.db[Collections.PROFILES].find_one(
            {"user_id": user["id"]}, {"_id": 0}
        )
        
        return PostResponse(
            id=post_id,
            user_id=user["id"],
            user_name=user["display_name"],
            user_handle=user["handle"],
            user_avatar=profile.get("avatar_url") if profile else None,
            type=request.type,
            content=request.content,
            media_urls=request.media_urls or [],
            tags=request.tags or [],
            reactions_count=0,
            comments_count=0,
            shares_count=0,
            user_reaction=None,
            created_at=now
        )
    
    async def get_post(self, post_id: str, current_user_id: str) -> PostResponse:
        """Get a single post."""
        post = await self.post_repo.find_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        return await self._enrich_post(post, current_user_id)
    
    async def get_feed(
        self, 
        current_user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[PostResponse]:
        """Get personalized feed."""
        # Get following list + self
        follows = await self.db[Collections.FOLLOWS].find(
            {"follower_id": current_user_id},
            {"_id": 0, "following_id": 1}
        ).to_list(1000)
        
        user_ids = [f["following_id"] for f in follows]
        user_ids.append(current_user_id)
        
        posts = await self.post_repo.get_feed(user_ids, limit, offset)
        
        return [await self._enrich_post(post, current_user_id) for post in posts]
    
    async def get_explore(
        self, 
        current_user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[PostResponse]:
        """Get explore/trending posts."""
        posts = await self.post_repo.get_explore(limit, offset)
        return [await self._enrich_post(post, current_user_id) for post in posts]
    
    async def get_user_posts(
        self, 
        user_id: str, 
        current_user_id: str,
        limit: int = 20, 
        offset: int = 0
    ) -> List[PostResponse]:
        """Get posts by a user."""
        posts = await self.post_repo.get_user_posts(user_id, limit, offset)
        return [await self._enrich_post(post, current_user_id) for post in posts]
    
    async def react_to_post(
        self, 
        post_id: str, 
        user: dict, 
        request: ReactionRequest
    ) -> ReactionResponse:
        """React to a post."""
        post = await self.post_repo.find_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        now = utc_now_iso()
        existing = await self.reaction_repo.find_user_reaction(post_id, user["id"])
        
        if existing:
            if existing["reaction_type"] == request.reaction_type:
                # Remove reaction
                await self.reaction_repo.delete(existing["id"])
                await self.post_repo.increment_count(post_id, "reactions_count", -1)
                
                new_count = post.get("reactions_count", 1) - 1
                return ReactionResponse(
                    ok=True,
                    action="removed",
                    reaction_type=None,
                    reactions_count=max(0, new_count)
                )
            else:
                # Update reaction
                await self.reaction_repo.update(
                    existing["id"], 
                    request.reaction_type, 
                    now
                )
                return ReactionResponse(
                    ok=True,
                    action="updated",
                    reaction_type=request.reaction_type,
                    reactions_count=post.get("reactions_count", 0)
                )
        else:
            # Add new reaction
            reaction_data = {
                "id": generate_id(),
                "post_id": post_id,
                "user_id": user["id"],
                "reaction_type": request.reaction_type,
                "created_at": now,
            }
            await self.reaction_repo.create(reaction_data)
            await self.post_repo.increment_count(post_id, "reactions_count", 1)
            
            # Create notification if not own post
            if post["user_id"] != user["id"]:
                notification = {
                    "id": generate_id(),
                    "user_id": post["user_id"],
                    "type": NotificationType.LIKE.value,
                    "title": "New Reaction",
                    "body": f"{user['display_name']} reacted to your post",
                    "data": {"post_id": post_id, "reaction_type": request.reaction_type},
                    "read": False,
                    "created_at": now,
                }
                await self.db[Collections.NOTIFICATIONS].insert_one(notification)
            
            new_count = post.get("reactions_count", 0) + 1
            return ReactionResponse(
                ok=True,
                action="added",
                reaction_type=request.reaction_type,
                reactions_count=new_count
            )
    
    async def _enrich_post(self, post: dict, current_user_id: str) -> PostResponse:
        """Add user info and reaction status to post."""
        user = await self.db[Collections.USERS].find_one(
            {"id": post["user_id"]}, {"_id": 0}
        )
        profile = await self.db[Collections.PROFILES].find_one(
            {"user_id": post["user_id"]}, {"_id": 0}
        )
        
        user_reaction = await self.reaction_repo.find_user_reaction(
            post["id"], current_user_id
        )
        
        return PostResponse(
            id=post["id"],
            user_id=post["user_id"],
            user_name=user.get("display_name", "Unknown") if user else "Unknown",
            user_handle=user.get("handle", "unknown") if user else "unknown",
            user_avatar=profile.get("avatar_url") if profile else None,
            type=post["type"],
            content=post["content"],
            media_urls=post.get("media_urls", []),
            tags=post.get("tags", []),
            reactions_count=post.get("reactions_count", 0),
            comments_count=post.get("comments_count", 0),
            shares_count=post.get("shares_count", 0),
            user_reaction=user_reaction.get("reaction_type") if user_reaction else None,
            created_at=post["created_at"]
        )


class CommentService:
    """Service for comment operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.comment_repo = CommentRepository(db)
        self.post_repo = PostRepository(db)
    
    async def create_comment(
        self, 
        post_id: str, 
        user: dict, 
        request: CommentCreateRequest
    ) -> CommentResponse:
        """Create a comment on a post."""
        post = await self.post_repo.find_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        now = utc_now_iso()
        comment_id = generate_id()
        
        # If replying to a comment, validate parent exists
        if request.parent_id:
            parent = await self.comment_repo.find_by_id(request.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent comment not found"
                )
            await self.comment_repo.increment_replies(request.parent_id, 1)
        
        comment_data = {
            "id": comment_id,
            "post_id": post_id,
            "user_id": user["id"],
            "content": request.content,
            "parent_id": request.parent_id,
            "replies_count": 0,
            "created_at": now,
        }
        
        await self.comment_repo.create(comment_data)
        
        # Update post comments count
        await self.post_repo.increment_count(post_id, "comments_count", 1)
        
        # Create notification
        if post["user_id"] != user["id"]:
            notification = {
                "id": generate_id(),
                "user_id": post["user_id"],
                "type": NotificationType.COMMENT.value,
                "title": "New Comment",
                "body": f"{user['display_name']} commented on your post",
                "data": {"post_id": post_id, "comment_id": comment_id},
                "read": False,
                "created_at": now,
            }
            await self.db[Collections.NOTIFICATIONS].insert_one(notification)
        
        profile = await self.db[Collections.PROFILES].find_one(
            {"user_id": user["id"]}, {"_id": 0}
        )
        
        return CommentResponse(
            id=comment_id,
            post_id=post_id,
            user_id=user["id"],
            user_name=user["display_name"],
            user_handle=user["handle"],
            user_avatar=profile.get("avatar_url") if profile else None,
            content=request.content,
            parent_id=request.parent_id,
            replies_count=0,
            created_at=now
        )
    
    async def get_comments(
        self, 
        post_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[CommentResponse]:
        """Get comments on a post."""
        comments = await self.comment_repo.get_post_comments(post_id, limit, offset)
        
        result = []
        for comment in comments:
            user = await self.db[Collections.USERS].find_one(
                {"id": comment["user_id"]}, {"_id": 0}
            )
            profile = await self.db[Collections.PROFILES].find_one(
                {"user_id": comment["user_id"]}, {"_id": 0}
            )
            
            result.append(CommentResponse(
                id=comment["id"],
                post_id=comment["post_id"],
                user_id=comment["user_id"],
                user_name=user.get("display_name", "Unknown") if user else "Unknown",
                user_handle=user.get("handle", "unknown") if user else "unknown",
                user_avatar=profile.get("avatar_url") if profile else None,
                content=comment["content"],
                parent_id=comment.get("parent_id"),
                replies_count=comment.get("replies_count", 0),
                created_at=comment["created_at"]
            ))
        
        return result


class StoryService:
    """Service for story operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.story_repo = StoryRepository(db)
    
    async def create_story(self, user: dict, request: StoryCreateRequest) -> StoryResponse:
        """Create a new story."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=settings.STORY_DURATION_HOURS)
        story_id = generate_id()
        
        story_data = {
            "id": story_id,
            "user_id": user["id"],
            "media_url": request.media_url,
            "media_type": request.media_type,
            "caption": request.caption,
            "duration": request.duration,
            "views_count": 0,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        }
        
        await self.story_repo.create(story_data)
        
        profile = await self.db[Collections.PROFILES].find_one(
            {"user_id": user["id"]}, {"_id": 0}
        )
        
        return StoryResponse(
            id=story_id,
            user_id=user["id"],
            user_name=user["display_name"],
            user_handle=user["handle"],
            user_avatar=profile.get("avatar_url") if profile else None,
            media_url=request.media_url,
            media_type=request.media_type,
            caption=request.caption,
            duration=request.duration,
            views_count=0,
            has_viewed=False,
            created_at=now.isoformat(),
            expires_at=expires.isoformat()
        )
    
    async def get_stories_feed(
        self, 
        current_user_id: str
    ) -> List[StoryGroupResponse]:
        """Get stories from followed users grouped by user."""
        # Get following + self
        follows = await self.db[Collections.FOLLOWS].find(
            {"follower_id": current_user_id},
            {"_id": 0, "following_id": 1}
        ).to_list(1000)
        
        user_ids = [f["following_id"] for f in follows]
        user_ids.append(current_user_id)
        
        stories = await self.story_repo.get_active_stories(user_ids)
        
        # Group by user
        user_stories = {}
        for story in stories:
            uid = story["user_id"]
            if uid not in user_stories:
                user_stories[uid] = []
            user_stories[uid].append(story)
        
        result = []
        for uid, stories_list in user_stories.items():
            user = await self.db[Collections.USERS].find_one({"id": uid}, {"_id": 0})
            profile = await self.db[Collections.PROFILES].find_one({"user_id": uid}, {"_id": 0})
            
            story_responses = []
            has_unseen = False
            
            for story in stories_list:
                has_viewed = await self.story_repo.has_viewed(story["id"], current_user_id)
                if not has_viewed:
                    has_unseen = True
                
                story_responses.append(StoryResponse(
                    id=story["id"],
                    user_id=story["user_id"],
                    user_name=user.get("display_name", "Unknown") if user else "Unknown",
                    user_handle=user.get("handle", "unknown") if user else "unknown",
                    user_avatar=profile.get("avatar_url") if profile else None,
                    media_url=story["media_url"],
                    media_type=story["media_type"],
                    caption=story.get("caption"),
                    duration=story["duration"],
                    views_count=story.get("views_count", 0),
                    has_viewed=has_viewed,
                    created_at=story["created_at"],
                    expires_at=story["expires_at"]
                ))
            
            result.append(StoryGroupResponse(
                user_id=uid,
                user_name=user.get("display_name", "Unknown") if user else "Unknown",
                user_handle=user.get("handle", "unknown") if user else "unknown",
                user_avatar=profile.get("avatar_url") if profile else None,
                stories=story_responses,
                has_unseen=has_unseen
            ))
        
        # Sort by unseen first
        result.sort(key=lambda x: (not x.has_unseen, x.stories[0].created_at if x.stories else ""))
        
        return result
    
    async def view_story(self, story_id: str, viewer_id: str) -> bool:
        """Mark a story as viewed."""
        story = await self.story_repo.find_by_id(story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        now = utc_now_iso()
        return await self.story_repo.record_view(story_id, viewer_id, now)
