"""
Meet module - Dating features with squad-first matching.
"""
from .router import router
from .service import (
    MeetAccessService, DatingProfileService, SquadService,
    DiscoveryService, SwipeService
)
from .repository import (
    MeetAccessRepository, DatingProfileRepository, SquadRepository,
    SquadMemberRepository, SquadInviteRepository, SwipeRepository,
    VoteRepository, MatchRepository
)
from .schemas import (
    MeetStatusResponse, AgeAssureResponse,
    DatingProfileRequest, DatingProfileResponse,
    SquadCreateRequest, SquadResponse, SquadMemberResponse,
    SquadInviteRequest, SquadInviteResponse,
    SwipeRequest, SwipeResponse,
    VoteRequest, VoteResponse,
    MatchResponse, DiscoverSquadResponse
)

__all__ = [
    "router",
    "MeetAccessService", "DatingProfileService", "SquadService",
    "DiscoveryService", "SwipeService",
    "MeetAccessRepository", "DatingProfileRepository", "SquadRepository",
    "SquadMemberRepository", "SquadInviteRepository", "SwipeRepository",
    "VoteRepository", "MatchRepository",
    "MeetStatusResponse", "AgeAssureResponse",
    "DatingProfileRequest", "DatingProfileResponse",
    "SquadCreateRequest", "SquadResponse", "SquadMemberResponse",
    "SquadInviteRequest", "SquadInviteResponse",
    "SwipeRequest", "SwipeResponse",
    "VoteRequest", "VoteResponse",
    "MatchResponse", "DiscoverSquadResponse"
]
