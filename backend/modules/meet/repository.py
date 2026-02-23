"""
Meet module - Repository for dating data access.
"""
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.database import Collections


class MeetAccessRepository:
    """Repository for meet access data."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.MEET_ACCESS]
    
    async def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"user_id": user_id}, {"_id": 0})
    
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0


class DatingProfileRepository:
    """Repository for dating profiles."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.DATING_PROFILES]
    
    async def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"user_id": user_id}, {"_id": 0})
    
    async def upsert(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$set": profile_data},
            upsert=True
        )
        return result.acknowledged
    
    async def get_multiple_by_user_ids(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"user_id": {"$in": user_ids}}, {"_id": 0})
        return await cursor.to_list(len(user_ids))


class SquadRepository:
    """Repository for squads."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.SQUADS]
    
    async def find_by_id(self, squad_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"id": squad_id}, {"_id": 0})
    
    async def create(self, squad_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.collection.insert_one(squad_data)
        return {k: v for k, v in squad_data.items() if k != "_id"}
    
    async def update_elo(self, squad_id: str, elo: int) -> bool:
        result = await self.collection.update_one(
            {"id": squad_id},
            {"$set": {"squad_elo": elo}}
        )
        return result.modified_count > 0
    
    async def get_by_ids(self, squad_ids: List[str]) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"id": {"$in": squad_ids}}, {"_id": 0})
        return await cursor.to_list(len(squad_ids))
    
    async def get_discoverable(
        self, 
        exclude_ids: List[str], 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get squads for discovery, excluding certain IDs."""
        cursor = self.collection.find(
            {"id": {"$nin": exclude_ids}},
            {"_id": 0}
        ).limit(limit)
        return await cursor.to_list(limit)


class SquadMemberRepository:
    """Repository for squad members."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.SQUAD_MEMBERS]
    
    async def find_membership(self, squad_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({
            "squad_id": squad_id,
            "user_id": user_id
        }, {"_id": 0})
    
    async def get_user_memberships(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}, {"_id": 0})
        return await cursor.to_list(100)
    
    async def get_squad_members(self, squad_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"squad_id": squad_id}, {"_id": 0})
        return await cursor.to_list(10)
    
    async def count_members(self, squad_id: str) -> int:
        return await self.collection.count_documents({"squad_id": squad_id})
    
    async def create(self, member_data: Dict[str, Any]) -> bool:
        await self.collection.insert_one(member_data)
        return True


class SquadInviteRepository:
    """Repository for squad invites."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.SQUAD_INVITES]
    
    async def find_by_id(self, invite_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"id": invite_id}, {"_id": 0})
    
    async def find_pending(self, squad_id: str, invitee_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({
            "squad_id": squad_id,
            "invitee_id": invitee_id,
            "status": "pending"
        }, {"_id": 0})
    
    async def get_user_invites(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({
            "invitee_id": user_id,
            "status": "pending"
        }, {"_id": 0})
        return await cursor.to_list(100)
    
    async def create(self, invite_data: Dict[str, Any]) -> bool:
        await self.collection.insert_one(invite_data)
        return True
    
    async def update_status(self, invite_id: str, status: str, updated_at: str) -> bool:
        result = await self.collection.update_one(
            {"id": invite_id},
            {"$set": {"status": status, "updated_at": updated_at}}
        )
        return result.modified_count > 0


class SwipeRepository:
    """Repository for swipes."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.SQUAD_SWIPES]
    
    async def find_by_id(self, swipe_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"id": swipe_id}, {"_id": 0})
    
    async def find_swipe(self, squad_id: str, target_squad_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({
            "squad_id": squad_id,
            "target_squad_id": target_squad_id
        }, {"_id": 0})
    
    async def find_reciprocal(self, squad_id: str, target_squad_id: str) -> Optional[Dict[str, Any]]:
        """Find if target squad has liked us."""
        return await self.collection.find_one({
            "squad_id": target_squad_id,
            "target_squad_id": squad_id,
            "outcome": "liked"
        }, {"_id": 0})
    
    async def get_swiped_ids(self, squad_ids: List[str]) -> List[str]:
        """Get IDs of squads already swiped by any of the given squads."""
        cursor = self.collection.find(
            {"squad_id": {"$in": squad_ids}},
            {"_id": 0, "target_squad_id": 1}
        )
        swipes = await cursor.to_list(1000)
        return [s["target_squad_id"] for s in swipes]
    
    async def create(self, swipe_data: Dict[str, Any]) -> bool:
        await self.collection.insert_one(swipe_data)
        return True
    
    async def update_outcome(self, swipe_id: str, outcome: str) -> bool:
        result = await self.collection.update_one(
            {"id": swipe_id},
            {"$set": {"outcome": outcome}}
        )
        return result.modified_count > 0


class VoteRepository:
    """Repository for swipe votes."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.SQUAD_SWIPE_VOTES]
    
    async def find_vote(self, swipe_id: str, voter_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({
            "swipe_id": swipe_id,
            "voter_user_id": voter_id
        }, {"_id": 0})
    
    async def create(self, vote_data: Dict[str, Any]) -> bool:
        await self.collection.insert_one(vote_data)
        return True
    
    async def update(self, vote_id: str, vote: str, updated_at: str) -> bool:
        result = await self.collection.update_one(
            {"id": vote_id},
            {"$set": {"vote": vote, "updated_at": updated_at}}
        )
        return result.modified_count > 0
    
    async def count_by_type(self, swipe_id: str, vote_type: str) -> int:
        return await self.collection.count_documents({
            "swipe_id": swipe_id,
            "vote": vote_type
        })


class MatchRepository:
    """Repository for squad matches."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.SQUAD_MATCHES]
    
    async def find_match(self, squad_a_id: str, squad_b_id: str) -> Optional[Dict[str, Any]]:
        # Always use sorted order
        a, b = (squad_a_id, squad_b_id) if squad_a_id < squad_b_id else (squad_b_id, squad_a_id)
        return await self.collection.find_one({
            "squad_a_id": a,
            "squad_b_id": b
        }, {"_id": 0})
    
    async def create(self, match_data: Dict[str, Any]) -> bool:
        await self.collection.insert_one(match_data)
        return True
    
    async def get_user_matches(self, squad_ids: List[str]) -> List[Dict[str, Any]]:
        """Get matches for any of the given squad IDs."""
        cursor = self.collection.find({
            "$or": [
                {"squad_a_id": {"$in": squad_ids}},
                {"squad_b_id": {"$in": squad_ids}}
            ]
        }, {"_id": 0})
        return await cursor.to_list(100)
