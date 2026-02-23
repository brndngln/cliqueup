"""
Meet module - API router for dating features.
"""
from fastapi import APIRouter, Depends, Query
from typing import List

from ...core.database import Database
from ...core.security import get_current_user
from .schemas import (
    MeetStatusResponse, AgeAssureResponse,
    DatingProfileRequest, DatingProfileResponse,
    SquadCreateRequest, SquadResponse,
    SquadInviteRequest, SquadInviteResponse,
    SwipeRequest, SwipeResponse,
    VoteRequest, VoteResponse,
    MatchResponse, DiscoverSquadResponse
)
from .service import (
    MeetAccessService, DatingProfileService, SquadService,
    DiscoveryService, SwipeService
)

router = APIRouter(prefix="/meet", tags=["Meet (Dating)"])


def get_meet_access_service() -> MeetAccessService:
    return MeetAccessService(Database.get_db())


def get_dating_profile_service() -> DatingProfileService:
    return DatingProfileService(Database.get_db())


def get_squad_service() -> SquadService:
    return SquadService(Database.get_db())


def get_discovery_service() -> DiscoveryService:
    return DiscoveryService(Database.get_db())


def get_swipe_service() -> SwipeService:
    return SwipeService(Database.get_db())


# ==================== Meet Access ====================

@router.get("/status", response_model=MeetStatusResponse)
async def get_meet_status(
    current_user: dict = Depends(get_current_user),
    service: MeetAccessService = Depends(get_meet_access_service)
):
    """Check if Meet (dating) is unlocked for the user."""
    return await service.get_status(current_user)


@router.post("/age-assure", response_model=AgeAssureResponse)
async def age_assure(
    current_user: dict = Depends(get_current_user),
    service: MeetAccessService = Depends(get_meet_access_service)
):
    """Complete age verification to unlock Meet (mocked)."""
    return await service.age_assure(current_user)


# ==================== Dating Profile ====================

@router.get("/dating-profile", response_model=DatingProfileResponse)
async def get_my_dating_profile(
    current_user: dict = Depends(get_current_user),
    service: DatingProfileService = Depends(get_dating_profile_service)
):
    """Get current user's dating profile."""
    return await service.get_profile(current_user["id"])


@router.post("/dating-profile", response_model=DatingProfileResponse)
async def create_or_update_dating_profile(
    request: DatingProfileRequest,
    current_user: dict = Depends(get_current_user),
    service: DatingProfileService = Depends(get_dating_profile_service)
):
    """Create or update dating profile."""
    return await service.create_or_update_profile(current_user, request)


@router.get("/dating-profile/{user_id}", response_model=DatingProfileResponse)
async def get_dating_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: DatingProfileService = Depends(get_dating_profile_service)
):
    """Get another user's dating profile."""
    return await service.get_profile(user_id)


# ==================== Squads ====================

@router.post("/squads", response_model=SquadResponse)
async def create_squad(
    request: SquadCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: SquadService = Depends(get_squad_service)
):
    """Create a new squad for group dating."""
    return await service.create_squad(current_user, request)


@router.get("/squads", response_model=List[SquadResponse])
async def get_my_squads(
    current_user: dict = Depends(get_current_user),
    service: SquadService = Depends(get_squad_service)
):
    """Get all squads the user belongs to."""
    return await service.get_user_squads(current_user["id"])


@router.get("/squads/{squad_id}", response_model=SquadResponse)
async def get_squad(
    squad_id: str,
    current_user: dict = Depends(get_current_user),
    service: SquadService = Depends(get_squad_service)
):
    """Get a specific squad."""
    return await service.get_squad(squad_id)


@router.post("/squads/{squad_id}/invite", response_model=SquadInviteResponse)
async def invite_to_squad(
    squad_id: str,
    request: SquadInviteRequest,
    current_user: dict = Depends(get_current_user),
    service: SquadService = Depends(get_squad_service)
):
    """Invite a user to your squad (owner only)."""
    return await service.invite_to_squad(squad_id, current_user, request)


# ==================== Invites ====================

@router.get("/invites", response_model=List[SquadInviteResponse])
async def get_my_invites(
    current_user: dict = Depends(get_current_user),
    service: SquadService = Depends(get_squad_service)
):
    """Get pending squad invites for the user."""
    return await service.get_user_invites(current_user["id"])


@router.post("/squads/{squad_id}/invite/{invite_id}/accept")
async def accept_invite(
    squad_id: str,
    invite_id: str,
    current_user: dict = Depends(get_current_user),
    service: SquadService = Depends(get_squad_service)
):
    """Accept a squad invite."""
    return await service.accept_invite(invite_id, current_user)


@router.post("/squads/{squad_id}/invite/{invite_id}/decline")
async def decline_invite(
    squad_id: str,
    invite_id: str,
    current_user: dict = Depends(get_current_user),
    service: SquadService = Depends(get_squad_service)
):
    """Decline a squad invite."""
    return await service.decline_invite(invite_id, current_user)


# ==================== Discovery ====================

@router.get("/discover", response_model=List[DiscoverSquadResponse])
async def discover_squads(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Discover squads to swipe on.
    
    Squads are ranked by Elo compatibility score.
    """
    return await service.discover_squads(current_user, limit)


# ==================== Swipes & Voting ====================

@router.post("/squads/{squad_id}/swipe", response_model=SwipeResponse)
async def swipe_on_squad(
    squad_id: str,
    request: SwipeRequest,
    current_user: dict = Depends(get_current_user),
    service: SwipeService = Depends(get_swipe_service)
):
    """Create a swipe on a target squad."""
    return await service.swipe(squad_id, current_user, request)


@router.post("/swipes/{swipe_id}/vote", response_model=VoteResponse)
async def vote_on_swipe(
    swipe_id: str,
    request: VoteRequest,
    current_user: dict = Depends(get_current_user),
    service: SwipeService = Depends(get_swipe_service)
):
    """
    Vote on a swipe.
    
    - **like**: Approve the match
    - **pass**: Reject the match
    - **veto**: Block the match (if squad has veto enabled)
    """
    return await service.vote(swipe_id, current_user, request)


# ==================== Matches ====================

@router.get("/matches", response_model=List[MatchResponse])
async def get_matches(
    current_user: dict = Depends(get_current_user),
    service: SwipeService = Depends(get_swipe_service)
):
    """Get all matches for the user's squads."""
    return await service.get_matches(current_user["id"])
