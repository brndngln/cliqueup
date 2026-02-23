"""
Meet module - Service layer for dating features.
Includes Elo-based matching algorithm.
"""
from typing import Optional, List
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.database import Collections
from ...core.config import settings
from ...core.enums import (
    AgeBand, DatingTier, SquadMemberRole, InviteStatus,
    SwipeDirection, SwipeOutcome, VoteType, ConversationType, NotificationType
)
from ...utils.helpers import generate_id, utc_now_iso, get_squad_cap, get_required_likes
from ...utils.elo import EloRating
from .repository import (
    MeetAccessRepository, DatingProfileRepository, SquadRepository,
    SquadMemberRepository, SquadInviteRepository, SwipeRepository,
    VoteRepository, MatchRepository
)
from .schemas import (
    MeetStatusResponse, AgeAssureResponse, DatingProfileRequest, DatingProfileResponse,
    SquadCreateRequest, SquadResponse, SquadMemberResponse,
    SquadInviteRequest, SquadInviteResponse,
    SwipeRequest, SwipeResponse, VoteRequest, VoteResponse,
    MatchResponse, DiscoverSquadResponse
)


class MeetAccessService:
    """Service for meet access management."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.access_repo = MeetAccessRepository(db)
    
    async def get_status(self, user: dict) -> MeetStatusResponse:
        """Get user's meet access status."""
        if user["age_band"] != AgeBand.ADULT.value:
            return MeetStatusResponse(
                meet_locked=True,
                reason="Meet is only available for users 18+",
                age_assured_18plus=False,
                meet_enabled=False
            )
        
        access = await self.access_repo.find_by_user_id(user["id"])
        if not access or not access.get("age_assured_18plus"):
            return MeetStatusResponse(
                meet_locked=True,
                reason="Please complete age verification to unlock Meet",
                age_assured_18plus=False,
                meet_enabled=False
            )
        
        return MeetStatusResponse(
            meet_locked=False,
            reason="Meet is unlocked",
            age_assured_18plus=True,
            meet_enabled=access.get("meet_enabled", False)
        )
    
    async def age_assure(self, user: dict) -> AgeAssureResponse:
        """Complete age verification (mocked)."""
        if user["age_band"] != AgeBand.ADULT.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Meet is only available for users 18+"
            )
        
        now = utc_now_iso()
        await self.access_repo.update(user["id"], {
            "age_assured_18plus": True,
            "meet_enabled": True,
            "updated_at": now
        })
        
        return AgeAssureResponse(
            age_assured_18plus=True,
            meet_enabled=True
        )
    
    async def check_meet_access(self, user: dict) -> None:
        """Helper to check and raise if meet is locked."""
        meet_status = await self.get_status(user)
        if meet_status.meet_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=meet_status.reason
            )


class DatingProfileService:
    """Service for dating profile management."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.profile_repo = DatingProfileRepository(db)
        self.access_service = MeetAccessService(db)
    
    async def get_profile(self, user_id: str) -> DatingProfileResponse:
        """Get dating profile."""
        profile = await self.profile_repo.find_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dating profile not found"
            )
        
        user = await self.db[Collections.USERS].find_one({"id": user_id}, {"_id": 0})
        
        return DatingProfileResponse(
            **profile,
            elo_rating=user.get("elo_rating", settings.DEFAULT_ELO) if user else settings.DEFAULT_ELO
        )
    
    async def create_or_update_profile(
        self, 
        user: dict, 
        request: DatingProfileRequest
    ) -> DatingProfileResponse:
        """Create or update dating profile."""
        await self.access_service.check_meet_access(user)
        
        now = utc_now_iso()
        profile_data = {
            "user_id": user["id"],
            "intent": request.intent,
            "bio": request.bio,
            "prompts": request.prompts or [],
            "photos": request.photos or [],
            "preferences": request.preferences or {},
            "photo_verified": False,
            "id_verified": False,
            "updated_at": now,
        }
        
        await self.profile_repo.upsert(user["id"], profile_data)
        
        return DatingProfileResponse(
            **profile_data,
            elo_rating=user.get("elo_rating", settings.DEFAULT_ELO)
        )


class SquadService:
    """Service for squad management with Elo-based matching."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.squad_repo = SquadRepository(db)
        self.member_repo = SquadMemberRepository(db)
        self.invite_repo = SquadInviteRepository(db)
        self.swipe_repo = SwipeRepository(db)
        self.vote_repo = VoteRepository(db)
        self.match_repo = MatchRepository(db)
        self.dating_profile_repo = DatingProfileRepository(db)
        self.access_service = MeetAccessService(db)
    
    async def create_squad(self, user: dict, request: SquadCreateRequest) -> SquadResponse:
        """Create a new squad."""
        await self.access_service.check_meet_access(user)
        
        now = utc_now_iso()
        squad_id = generate_id()
        
        squad_data = {
            "id": squad_id,
            "owner_id": user["id"],
            "name": request.name,
            "visibility": request.visibility,
            "veto_enabled": request.veto_enabled,
            "squad_elo": user.get("elo_rating", settings.DEFAULT_ELO),
            "created_at": now,
            "updated_at": now,
        }
        
        await self.squad_repo.create(squad_data)
        
        # Add owner as member
        member_data = {
            "id": generate_id(),
            "squad_id": squad_id,
            "user_id": user["id"],
            "role": SquadMemberRole.OWNER.value,
            "joined_at": now,
        }
        await self.member_repo.create(member_data)
        
        profile = await self.db[Collections.PROFILES].find_one(
            {"user_id": user["id"]}, {"_id": 0}
        )
        
        return SquadResponse(
            id=squad_id,
            owner_id=user["id"],
            name=request.name,
            visibility=request.visibility,
            veto_enabled=request.veto_enabled,
            member_count=1,
            squad_elo=user.get("elo_rating", settings.DEFAULT_ELO),
            members=[SquadMemberResponse(
                user_id=user["id"],
                display_name=user["display_name"],
                avatar_url=profile.get("avatar_url") if profile else None,
                role=SquadMemberRole.OWNER.value,
                elo_rating=user.get("elo_rating", settings.DEFAULT_ELO)
            )],
            created_at=now
        )
    
    async def get_user_squads(self, user_id: str) -> List[SquadResponse]:
        """Get all squads a user belongs to."""
        memberships = await self.member_repo.get_user_memberships(user_id)
        squad_ids = [m["squad_id"] for m in memberships]
        
        if not squad_ids:
            return []
        
        squads = await self.squad_repo.get_by_ids(squad_ids)
        
        result = []
        for squad in squads:
            members = await self._get_squad_members(squad["id"])
            result.append(SquadResponse(
                id=squad["id"],
                owner_id=squad["owner_id"],
                name=squad["name"],
                visibility=squad["visibility"],
                veto_enabled=squad["veto_enabled"],
                member_count=len(members),
                squad_elo=squad.get("squad_elo", settings.DEFAULT_ELO),
                members=members,
                created_at=squad["created_at"]
            ))
        
        return result
    
    async def get_squad(self, squad_id: str) -> SquadResponse:
        """Get a single squad."""
        squad = await self.squad_repo.find_by_id(squad_id)
        if not squad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Squad not found"
            )
        
        members = await self._get_squad_members(squad_id)
        
        return SquadResponse(
            id=squad["id"],
            owner_id=squad["owner_id"],
            name=squad["name"],
            visibility=squad["visibility"],
            veto_enabled=squad["veto_enabled"],
            member_count=len(members),
            squad_elo=squad.get("squad_elo", settings.DEFAULT_ELO),
            members=members,
            created_at=squad["created_at"]
        )
    
    async def _get_squad_members(self, squad_id: str) -> List[SquadMemberResponse]:
        """Get squad members with user info."""
        members = await self.member_repo.get_squad_members(squad_id)
        result = []
        
        for m in members:
            user = await self.db[Collections.USERS].find_one(
                {"id": m["user_id"]}, {"_id": 0}
            )
            profile = await self.db[Collections.PROFILES].find_one(
                {"user_id": m["user_id"]}, {"_id": 0}
            )
            
            if user:
                result.append(SquadMemberResponse(
                    user_id=m["user_id"],
                    display_name=user.get("display_name", "Unknown"),
                    avatar_url=profile.get("avatar_url") if profile else None,
                    role=m["role"],
                    elo_rating=user.get("elo_rating", settings.DEFAULT_ELO)
                ))
        
        return result
    
    async def invite_to_squad(
        self, 
        squad_id: str, 
        user: dict, 
        request: SquadInviteRequest
    ) -> SquadInviteResponse:
        """Invite a user to a squad."""
        await self.access_service.check_meet_access(user)
        
        squad = await self.squad_repo.find_by_id(squad_id)
        if not squad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Squad not found"
            )
        
        if squad["owner_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only squad owner can invite"
            )
        
        # Check cap
        entitlement = await self.db[Collections.ENTITLEMENTS].find_one(
            {"user_id": user["id"]}, {"_id": 0}
        )
        cap = get_squad_cap(entitlement.get("dating_tier", "none") if entitlement else "none")
        member_count = await self.member_repo.count_members(squad_id)
        
        if member_count >= cap:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Squad is full (max {cap} members)"
            )
        
        # Check not already invited or member
        if await self.invite_repo.find_pending(squad_id, request.invitee_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already invited"
            )
        
        if await self.member_repo.find_membership(squad_id, request.invitee_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member"
            )
        
        now = utc_now_iso()
        invite_id = generate_id()
        
        invite_data = {
            "id": invite_id,
            "squad_id": squad_id,
            "inviter_id": user["id"],
            "invitee_id": request.invitee_id,
            "status": InviteStatus.PENDING.value,
            "created_at": now,
            "updated_at": now,
        }
        await self.invite_repo.create(invite_data)
        
        # Create notification
        notification = {
            "id": generate_id(),
            "user_id": request.invitee_id,
            "type": NotificationType.SQUAD_INVITE.value,
            "title": "Squad Invite",
            "body": f"{user['display_name']} invited you to join {squad['name']}",
            "data": {"squad_id": squad_id, "invite_id": invite_id},
            "read": False,
            "created_at": now,
        }
        await self.db[Collections.NOTIFICATIONS].insert_one(notification)
        
        return SquadInviteResponse(
            id=invite_id,
            squad_id=squad_id,
            squad_name=squad["name"],
            inviter_id=user["id"],
            inviter_name=user["display_name"],
            invitee_id=request.invitee_id,
            status=InviteStatus.PENDING.value,
            created_at=now
        )
    
    async def get_user_invites(self, user_id: str) -> List[SquadInviteResponse]:
        """Get pending invites for a user."""
        invites = await self.invite_repo.get_user_invites(user_id)
        
        result = []
        for invite in invites:
            squad = await self.squad_repo.find_by_id(invite["squad_id"])
            inviter = await self.db[Collections.USERS].find_one(
                {"id": invite["inviter_id"]}, {"_id": 0}
            )
            
            if squad and inviter:
                result.append(SquadInviteResponse(
                    id=invite["id"],
                    squad_id=invite["squad_id"],
                    squad_name=squad["name"],
                    inviter_id=invite["inviter_id"],
                    inviter_name=inviter["display_name"],
                    invitee_id=invite["invitee_id"],
                    status=invite["status"],
                    created_at=invite["created_at"]
                ))
        
        return result
    
    async def accept_invite(self, invite_id: str, user: dict) -> dict:
        """Accept a squad invite."""
        invite = await self.invite_repo.find_by_id(invite_id)
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invite not found"
            )
        
        if invite["invitee_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invite is not for you"
            )
        
        await self.access_service.check_meet_access(user)
        
        # Check cap again
        squad = await self.squad_repo.find_by_id(invite["squad_id"])
        entitlement = await self.db[Collections.ENTITLEMENTS].find_one(
            {"user_id": squad["owner_id"]}, {"_id": 0}
        )
        cap = get_squad_cap(entitlement.get("dating_tier", "none") if entitlement else "none")
        member_count = await self.member_repo.count_members(invite["squad_id"])
        
        if member_count >= cap:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Squad is full (max {cap} members)"
            )
        
        now = utc_now_iso()
        
        # Update invite
        await self.invite_repo.update_status(invite_id, InviteStatus.ACCEPTED.value, now)
        
        # Add as member
        member_data = {
            "id": generate_id(),
            "squad_id": invite["squad_id"],
            "user_id": user["id"],
            "role": SquadMemberRole.MEMBER.value,
            "joined_at": now,
        }
        await self.member_repo.create(member_data)
        
        # Recalculate squad Elo
        await self._recalculate_squad_elo(invite["squad_id"])
        
        return {
            "ok": True,
            "squad_id": invite["squad_id"],
            "user_id": user["id"],
            "role": SquadMemberRole.MEMBER.value
        }
    
    async def decline_invite(self, invite_id: str, user: dict) -> dict:
        """Decline a squad invite."""
        invite = await self.invite_repo.find_by_id(invite_id)
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invite not found"
            )
        
        if invite["invitee_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invite is not for you"
            )
        
        now = utc_now_iso()
        await self.invite_repo.update_status(invite_id, InviteStatus.DECLINED.value, now)
        
        return {"ok": True}
    
    async def _recalculate_squad_elo(self, squad_id: str) -> int:
        """Recalculate and update squad Elo based on members."""
        members = await self.member_repo.get_squad_members(squad_id)
        member_elos = []
        
        for m in members:
            user = await self.db[Collections.USERS].find_one(
                {"id": m["user_id"]}, {"_id": 0}
            )
            if user:
                member_elos.append(user.get("elo_rating", settings.DEFAULT_ELO))
        
        squad_elo = EloRating.calculate_squad_rating(member_elos)
        await self.squad_repo.update_elo(squad_id, squad_elo)
        
        return squad_elo


class DiscoveryService:
    """Service for squad discovery with Elo-based ranking."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.squad_repo = SquadRepository(db)
        self.member_repo = SquadMemberRepository(db)
        self.swipe_repo = SwipeRepository(db)
        self.dating_profile_repo = DatingProfileRepository(db)
        self.access_service = MeetAccessService(db)
    
    async def discover_squads(
        self, 
        user: dict, 
        limit: int = 10
    ) -> List[DiscoverSquadResponse]:
        """Get squads to swipe on, ranked by Elo compatibility."""
        await self.access_service.check_meet_access(user)
        
        # Get user's squads
        memberships = await self.member_repo.get_user_memberships(user["id"])
        my_squad_ids = [m["squad_id"] for m in memberships]
        
        # Get already swiped squads
        swiped_ids = await self.swipe_repo.get_swiped_ids(my_squad_ids)
        
        # Exclude own squads and already swiped
        exclude_ids = list(set(my_squad_ids + swiped_ids))
        
        # Get discoverable squads
        squads = await self.squad_repo.get_discoverable(exclude_ids, limit * 2)
        
        if not squads:
            return []
        
        # Calculate compatibility and rank
        user_elo = user.get("elo_rating", settings.DEFAULT_ELO)
        scored_squads = []
        
        for squad in squads:
            compatibility = EloRating.match_score(
                user_elo, 
                squad.get("squad_elo", settings.DEFAULT_ELO)
            )
            scored_squads.append((squad, compatibility))
        
        # Sort by compatibility (highest first)
        scored_squads.sort(key=lambda x: x[1], reverse=True)
        
        # Build response
        result = []
        for squad, compatibility in scored_squads[:limit]:
            members = await self.member_repo.get_squad_members(squad["id"])
            member_info = []
            
            for m in members:
                user_data = await self.db[Collections.USERS].find_one(
                    {"id": m["user_id"]}, {"_id": 0}
                )
                profile = await self.db[Collections.PROFILES].find_one(
                    {"user_id": m["user_id"]}, {"_id": 0}
                )
                dating_profile = await self.dating_profile_repo.find_by_user_id(m["user_id"])
                
                if user_data:
                    member_info.append({
                        "user_id": m["user_id"],
                        "display_name": user_data.get("display_name", "Unknown"),
                        "avatar_url": profile.get("avatar_url") if profile else None,
                        "bio": dating_profile.get("bio") if dating_profile else None,
                        "photos": dating_profile.get("photos", []) if dating_profile else [],
                    })
            
            result.append(DiscoverSquadResponse(
                id=squad["id"],
                name=squad["name"],
                member_count=len(members),
                squad_elo=squad.get("squad_elo", settings.DEFAULT_ELO),
                compatibility_score=round(compatibility, 2),
                members=member_info
            ))
        
        return result


class SwipeService:
    """Service for swipe and match operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.squad_repo = SquadRepository(db)
        self.member_repo = SquadMemberRepository(db)
        self.swipe_repo = SwipeRepository(db)
        self.vote_repo = VoteRepository(db)
        self.match_repo = MatchRepository(db)
        self.access_service = MeetAccessService(db)
    
    async def swipe(
        self, 
        squad_id: str, 
        user: dict, 
        request: SwipeRequest
    ) -> SwipeResponse:
        """Create a swipe on a target squad."""
        await self.access_service.check_meet_access(user)
        
        # Verify membership
        membership = await self.member_repo.find_membership(squad_id, user["id"])
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this squad"
            )
        
        if squad_id == request.target_squad_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot swipe on your own squad"
            )
        
        # Check if already swiped
        existing = await self.swipe_repo.find_swipe(squad_id, request.target_squad_id)
        if existing:
            return SwipeResponse(
                id=existing["id"],
                squad_id=existing["squad_id"],
                target_squad_id=existing["target_squad_id"],
                direction=existing["direction"],
                outcome=existing["outcome"]
            )
        
        now = utc_now_iso()
        swipe_id = generate_id()
        
        swipe_data = {
            "id": swipe_id,
            "squad_id": squad_id,
            "target_squad_id": request.target_squad_id,
            "direction": request.direction,
            "outcome": SwipeOutcome.PENDING.value,
            "created_at": now,
        }
        await self.swipe_repo.create(swipe_data)
        
        return SwipeResponse(
            id=swipe_id,
            squad_id=squad_id,
            target_squad_id=request.target_squad_id,
            direction=request.direction,
            outcome=SwipeOutcome.PENDING.value
        )
    
    async def vote(self, swipe_id: str, user: dict, request: VoteRequest) -> VoteResponse:
        """Cast a vote on a swipe."""
        await self.access_service.check_meet_access(user)
        
        swipe = await self.swipe_repo.find_by_id(swipe_id)
        if not swipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swipe not found"
            )
        
        # Verify membership in the swiping squad
        membership = await self.member_repo.find_membership(swipe["squad_id"], user["id"])
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of the swiping squad"
            )
        
        squad = await self.squad_repo.find_by_id(swipe["squad_id"])
        now = utc_now_iso()
        
        # Upsert vote
        existing_vote = await self.vote_repo.find_vote(swipe_id, user["id"])
        if existing_vote:
            await self.vote_repo.update(existing_vote["id"], request.vote, now)
        else:
            vote_data = {
                "id": generate_id(),
                "swipe_id": swipe_id,
                "voter_user_id": user["id"],
                "vote": request.vote,
                "created_at": now,
            }
            await self.vote_repo.create(vote_data)
        
        # Tally votes
        like_count = await self.vote_repo.count_by_type(swipe_id, VoteType.LIKE.value)
        pass_count = await self.vote_repo.count_by_type(swipe_id, VoteType.PASS.value)
        veto_count = await self.vote_repo.count_by_type(swipe_id, VoteType.VETO.value)
        
        member_count = await self.member_repo.count_members(swipe["squad_id"])
        required = get_required_likes(member_count)
        
        # Determine outcome
        outcome = SwipeOutcome.PENDING.value
        if squad and squad.get("veto_enabled") and veto_count > 0:
            outcome = SwipeOutcome.VETOED.value
        elif like_count >= required and swipe["direction"] == SwipeDirection.LIKE.value:
            outcome = SwipeOutcome.LIKED.value
        elif pass_count >= required or swipe["direction"] == SwipeDirection.PASS.value:
            outcome = SwipeOutcome.PASSED.value
        
        await self.swipe_repo.update_outcome(swipe_id, outcome)
        
        # Check for match
        match_created = False
        match_id = None
        
        if outcome == SwipeOutcome.LIKED.value:
            # Check for reciprocal like
            reciprocal = await self.swipe_repo.find_reciprocal(
                swipe["squad_id"], 
                swipe["target_squad_id"]
            )
            
            if reciprocal:
                # Create match
                match_result = await self._create_match(
                    swipe["squad_id"],
                    swipe["target_squad_id"],
                    user["id"]
                )
                match_created = match_result["created"]
                match_id = match_result.get("match_id")
                
                # Update Elo ratings based on match
                await self._update_elos_on_match(
                    swipe["squad_id"],
                    swipe["target_squad_id"]
                )
        
        return VoteResponse(
            swipe_id=swipe_id,
            voter_user_id=user["id"],
            vote=request.vote,
            outcome=outcome,
            like_count=like_count,
            pass_count=pass_count,
            veto_count=veto_count,
            required_likes=required,
            match_created=match_created,
            match_id=match_id
        )
    
    async def _create_match(
        self, 
        squad_a_id: str, 
        squad_b_id: str, 
        creator_id: str
    ) -> dict:
        """Create a match between two squads."""
        # Sort IDs for consistent storage
        a, b = (squad_a_id, squad_b_id) if squad_a_id < squad_b_id else (squad_b_id, squad_a_id)
        
        # Check if match already exists
        existing = await self.match_repo.find_match(a, b)
        if existing:
            return {"created": False, "match_id": existing["id"]}
        
        now = utc_now_iso()
        
        # Get all members from both squads
        members_a = await self.member_repo.get_squad_members(a)
        members_b = await self.member_repo.get_squad_members(b)
        all_member_ids = list(set(
            [m["user_id"] for m in members_a] + [m["user_id"] for m in members_b]
        ))
        
        # Create conversation
        conv_id = generate_id()
        conversation = {
            "id": conv_id,
            "type": ConversationType.MEET_GROUP.value,
            "name": None,
            "created_by": creator_id,
            "created_at": now,
            "updated_at": now,
        }
        await self.db[Collections.CONVERSATIONS].insert_one(conversation)
        
        # Add members to conversation
        for uid in all_member_ids:
            await self.db[Collections.CONVERSATION_MEMBERS].insert_one({
                "id": generate_id(),
                "conversation_id": conv_id,
                "user_id": uid,
                "joined_at": now,
            })
        
        # Create match
        match_id = generate_id()
        match_data = {
            "id": match_id,
            "squad_a_id": a,
            "squad_b_id": b,
            "conversation_id": conv_id,
            "matched_at": now,
        }
        await self.match_repo.create(match_data)
        
        # Create notifications
        squad_a = await self.squad_repo.find_by_id(a)
        squad_b = await self.squad_repo.find_by_id(b)
        
        for uid in all_member_ids:
            notification = {
                "id": generate_id(),
                "user_id": uid,
                "type": NotificationType.MATCH.value,
                "title": "New Match!",
                "body": f"{squad_a['name']} and {squad_b['name']} matched!",
                "data": {"match_id": match_id, "conversation_id": conv_id},
                "read": False,
                "created_at": now,
            }
            await self.db[Collections.NOTIFICATIONS].insert_one(notification)
        
        return {"created": True, "match_id": match_id}
    
    async def _update_elos_on_match(self, squad_a_id: str, squad_b_id: str) -> None:
        """Update Elo ratings for all members after a match."""
        squad_a = await self.squad_repo.find_by_id(squad_a_id)
        squad_b = await self.squad_repo.find_by_id(squad_b_id)
        
        elo_a = squad_a.get("squad_elo", settings.DEFAULT_ELO) if squad_a else settings.DEFAULT_ELO
        elo_b = squad_b.get("squad_elo", settings.DEFAULT_ELO) if squad_b else settings.DEFAULT_ELO
        
        # Get all members and update their individual Elos
        for squad_id, opponent_elo in [(squad_a_id, elo_b), (squad_b_id, elo_a)]:
            members = await self.member_repo.get_squad_members(squad_id)
            for m in members:
                user = await self.db[Collections.USERS].find_one(
                    {"id": m["user_id"]}, {"_id": 0}
                )
                if user:
                    current_elo = user.get("elo_rating", settings.DEFAULT_ELO)
                    new_elo = EloRating.update_rating(current_elo, opponent_elo, 1.0)
                    await self.db[Collections.USERS].update_one(
                        {"id": m["user_id"]},
                        {"$set": {"elo_rating": new_elo}}
                    )
    
    async def get_matches(self, user_id: str) -> List[MatchResponse]:
        """Get user's matches."""
        memberships = await self.member_repo.get_user_memberships(user_id)
        squad_ids = [m["squad_id"] for m in memberships]
        
        if not squad_ids:
            return []
        
        matches = await self.match_repo.get_user_matches(squad_ids)
        
        result = []
        for match in matches:
            squad_a = await self.squad_repo.find_by_id(match["squad_a_id"])
            squad_b = await self.squad_repo.find_by_id(match["squad_b_id"])
            
            # Get all members
            members_a = await self.member_repo.get_squad_members(match["squad_a_id"])
            members_b = await self.member_repo.get_squad_members(match["squad_b_id"])
            
            member_responses = []
            for m in members_a + members_b:
                user = await self.db[Collections.USERS].find_one(
                    {"id": m["user_id"]}, {"_id": 0}
                )
                profile = await self.db[Collections.PROFILES].find_one(
                    {"user_id": m["user_id"]}, {"_id": 0}
                )
                if user:
                    member_responses.append(SquadMemberResponse(
                        user_id=m["user_id"],
                        display_name=user.get("display_name", "Unknown"),
                        avatar_url=profile.get("avatar_url") if profile else None,
                        role=m["role"],
                        elo_rating=user.get("elo_rating", settings.DEFAULT_ELO)
                    ))
            
            result.append(MatchResponse(
                id=match["id"],
                squad_a_id=match["squad_a_id"],
                squad_b_id=match["squad_b_id"],
                squad_a_name=squad_a["name"] if squad_a else "Unknown",
                squad_b_name=squad_b["name"] if squad_b else "Unknown",
                conversation_id=match["conversation_id"],
                matched_at=match["matched_at"],
                members=member_responses
            ))
        
        return result
