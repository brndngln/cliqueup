"""
Meet module - Pydantic schemas for dating features.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ==================== Meet Access Schemas ====================

class MeetStatusResponse(BaseModel):
    """Meet (dating) access status."""
    meet_locked: bool
    reason: str
    age_assured_18plus: bool
    meet_enabled: bool


class AgeAssureResponse(BaseModel):
    """Age verification response."""
    age_assured_18plus: bool
    meet_enabled: bool


# ==================== Dating Profile Schemas ====================

class DatingProfileRequest(BaseModel):
    """Create/update dating profile."""
    intent: Optional[str] = None  # casual, serious, friends
    bio: Optional[str] = Field(None, max_length=500)
    prompts: Optional[List[dict]] = None  # [{question, answer}]
    photos: Optional[List[str]] = None
    preferences: Optional[dict] = None  # {gender_prefs, age_range, distance, interests}


class DatingProfileResponse(BaseModel):
    """Dating profile response."""
    user_id: str
    intent: Optional[str] = None
    bio: Optional[str] = None
    prompts: List[dict] = []
    photos: List[str] = []
    preferences: dict = {}
    photo_verified: bool = False
    id_verified: bool = False
    elo_rating: int = 1200
    
    class Config:
        from_attributes = True


# ==================== Squad Schemas ====================

class SquadCreateRequest(BaseModel):
    """Create a squad."""
    name: str = Field(min_length=1, max_length=50)
    visibility: str = "standard"  # standard, incognito
    veto_enabled: bool = False


class SquadMemberResponse(BaseModel):
    """Squad member info."""
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    role: str
    elo_rating: int = 1200


class SquadResponse(BaseModel):
    """Squad response."""
    id: str
    owner_id: str
    name: str
    visibility: str
    veto_enabled: bool
    member_count: int
    squad_elo: int = 1200
    members: List[SquadMemberResponse] = []
    created_at: str
    
    class Config:
        from_attributes = True


class SquadInviteRequest(BaseModel):
    """Invite user to squad."""
    invitee_id: str


class SquadInviteResponse(BaseModel):
    """Squad invite response."""
    id: str
    squad_id: str
    squad_name: str
    inviter_id: str
    inviter_name: str
    invitee_id: str
    status: str
    created_at: str


# ==================== Swipe & Match Schemas ====================

class SwipeRequest(BaseModel):
    """Swipe on a squad."""
    target_squad_id: str
    direction: str = "like"  # like, pass


class SwipeResponse(BaseModel):
    """Swipe response."""
    id: str
    squad_id: str
    target_squad_id: str
    direction: str
    outcome: str  # pending, liked, passed, vetoed


class VoteRequest(BaseModel):
    """Vote on a swipe."""
    vote: str = "like"  # like, pass, veto


class VoteResponse(BaseModel):
    """Vote response with outcome."""
    swipe_id: str
    voter_user_id: str
    vote: str
    outcome: str
    like_count: int
    pass_count: int
    veto_count: int
    required_likes: int
    match_created: bool = False
    match_id: Optional[str] = None


class MatchResponse(BaseModel):
    """Match response."""
    id: str
    squad_a_id: str
    squad_b_id: str
    squad_a_name: str
    squad_b_name: str
    conversation_id: str
    matched_at: str
    members: List[SquadMemberResponse] = []
    
    class Config:
        from_attributes = True


# ==================== Discovery Schemas ====================

class DiscoverSquadResponse(BaseModel):
    """Squad in discover feed."""
    id: str
    name: str
    member_count: int
    squad_elo: int = 1200
    compatibility_score: float = 0.5
    members: List[dict] = []  # Contains user dating profile info
