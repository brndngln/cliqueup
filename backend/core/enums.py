"""
Shared enumerations across the application.
Centralized enum definitions for type safety.
"""
from enum import Enum


class AgeBand(str, Enum):
    """User age bands for content/feature gating."""
    U13 = "u13"
    TEEN = "teen"
    ADULT = "adult"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    LIMITED = "limited"
    SUSPENDED = "suspended"
    BANNED = "banned"


class DatingTier(str, Enum):
    """Dating subscription tiers."""
    NONE = "none"
    PLUS = "plus"
    ELITE = "elite"


class DatingLinkMode(str, Enum):
    """How dating profile is linked to social."""
    CURATED = "curated"
    FULL = "full"
    NONE = "none"


class SquadVisibility(str, Enum):
    """Squad profile visibility."""
    STANDARD = "standard"
    INCOGNITO = "incognito"


class SquadMemberRole(str, Enum):
    """Role within a squad."""
    OWNER = "owner"
    MEMBER = "member"


class InviteStatus(str, Enum):
    """Squad invite status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class SwipeDirection(str, Enum):
    """Swipe direction."""
    LIKE = "like"
    PASS = "pass"


class SwipeOutcome(str, Enum):
    """Result of squad voting on a swipe."""
    PENDING = "pending"
    LIKED = "liked"
    PASSED = "passed"
    VETOED = "vetoed"


class VoteType(str, Enum):
    """Individual vote on a swipe."""
    LIKE = "like"
    PASS = "pass"
    VETO = "veto"


class ConversationType(str, Enum):
    """Type of conversation."""
    DM = "dm"
    GROUP = "group"
    MEET_GROUP = "meet_group"


class PostType(str, Enum):
    """Type of post content."""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    CAROUSEL = "carousel"


class MediaType(str, Enum):
    """Media content type."""
    IMAGE = "image"
    VIDEO = "video"


class NotificationType(str, Enum):
    """Notification types."""
    FOLLOW = "follow"
    SQUAD_INVITE = "squad_invite"
    MATCH = "match"
    MESSAGE = "message"
    LIKE = "like"
    COMMENT = "comment"
    MENTION = "mention"


class ReactionType(str, Enum):
    """Post reaction types."""
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"
