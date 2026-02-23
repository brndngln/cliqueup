from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone, date, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
import json
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'nexus-super-secret-change-me')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== ENUMS ====================

class AgeBand(str, Enum):
    u13 = "u13"
    teen = "teen"
    adult = "adult"

class UserStatus(str, Enum):
    active = "active"
    limited = "limited"
    suspended = "suspended"
    banned = "banned"

class DatingLinkMode(str, Enum):
    curated = "curated"
    full = "full"
    none = "none"

class DatingTier(str, Enum):
    none = "none"
    plus = "plus"
    elite = "elite"

class SquadVisibility(str, Enum):
    standard = "standard"
    incognito = "incognito"

class SquadMemberRole(str, Enum):
    owner = "owner"
    member = "member"

class InviteStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"

class SwipeDirection(str, Enum):
    like = "like"
    pass_ = "pass"

class SwipeOutcome(str, Enum):
    pending = "pending"
    liked = "liked"
    passed = "passed"
    vetoed = "vetoed"

class VoteType(str, Enum):
    like = "like"
    pass_ = "pass"
    veto = "veto"

class ConversationType(str, Enum):
    dm = "dm"
    group = "group"
    meet_group = "meet_group"

class PostType(str, Enum):
    text = "text"
    photo = "photo"
    video = "video"
    carousel = "carousel"

# ==================== SCHEMAS ====================

# Auth Schemas
class SignupRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_e164: Optional[str] = None
    password: str = Field(min_length=8)
    dob: str  # YYYY-MM-DD format
    country_code: Optional[str] = None
    display_name: str = Field(min_length=1, max_length=50)
    handle: str = Field(min_length=3, max_length=30)

class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_e164: Optional[str] = None
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    phone_e164: Optional[str] = None
    dob: str
    age_band: str
    status: str
    display_name: str
    handle: str
    created_at: str

# Profile Schemas
class ProfileUpdateRequest(BaseModel):
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
    user_id: str
    handle: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    is_private: bool
    dating_link_mode: str
    pronouns: Optional[str] = None
    interests: List[str] = []
    followers_count: int = 0
    following_count: int = 0

# Dating Profile Schemas
class DatingProfileRequest(BaseModel):
    intent: Optional[str] = None  # casual, serious, friends
    bio: Optional[str] = Field(None, max_length=500)
    prompts: Optional[List[dict]] = None  # [{question, answer}]
    photos: Optional[List[str]] = None
    preferences: Optional[dict] = None  # {gender_prefs, age_range, distance, interests}

class DatingProfileResponse(BaseModel):
    user_id: str
    intent: Optional[str] = None
    bio: Optional[str] = None
    prompts: List[dict] = []
    photos: List[str] = []
    preferences: dict = {}
    photo_verified: bool = False
    id_verified: bool = False

# Meet Status
class MeetStatusResponse(BaseModel):
    meet_locked: bool
    reason: str
    age_assured_18plus: bool
    meet_enabled: bool

# Squad Schemas
class SquadCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    visibility: str = "standard"
    veto_enabled: bool = False

class SquadResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    visibility: str
    veto_enabled: bool
    member_count: int
    members: List[dict] = []
    created_at: str

class SquadInviteRequest(BaseModel):
    invitee_id: str

class SquadInviteResponse(BaseModel):
    id: str
    squad_id: str
    squad_name: str
    inviter_id: str
    inviter_name: str
    invitee_id: str
    status: str
    created_at: str

class SwipeRequest(BaseModel):
    target_squad_id: str
    direction: str = "like"

class SwipeResponse(BaseModel):
    id: str
    squad_id: str
    target_squad_id: str
    direction: str
    outcome: str

class VoteRequest(BaseModel):
    vote: str = "like"

class VoteResponse(BaseModel):
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
    id: str
    squad_a_id: str
    squad_b_id: str
    squad_a_name: str
    squad_b_name: str
    conversation_id: str
    matched_at: str
    members: List[dict] = []

# Messaging Schemas
class ConversationResponse(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    created_by: str
    members: List[dict] = []
    last_message: Optional[dict] = None
    created_at: str
    updated_at: str

class MessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    sender_avatar: Optional[str] = None
    body: str
    created_at: str

# Post Schemas
class PostCreateRequest(BaseModel):
    type: str = "text"
    content: str = Field(max_length=5000)
    media_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class PostResponse(BaseModel):
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

class ReactionRequest(BaseModel):
    reaction_type: str = "like"  # like, love, laugh, wow, sad, angry

class CommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[str] = None

class CommentResponse(BaseModel):
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

# Story Schemas
class StoryCreateRequest(BaseModel):
    media_url: str
    media_type: str = "image"  # image, video
    caption: Optional[str] = None
    duration: int = 5  # seconds

class StoryResponse(BaseModel):
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
    created_at: str
    expires_at: str

# Notification Schema
class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    body: str
    data: dict = {}
    read: bool = False
    created_at: str

# ==================== HELPERS ====================

def compute_age_band(dob_str: str) -> AgeBand:
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if years < 13:
        return AgeBand.u13
    if years < 18:
        return AgeBand.teen
    return AgeBand.adult

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise credentials_exception
    return user

def get_required_likes(member_count: int) -> int:
    if member_count <= 2:
        return 2
    if member_count == 3:
        return 2
    if member_count == 4:
        return 3
    return 3  # 5+

def get_squad_cap(tier: str) -> int:
    if tier == DatingTier.elite.value:
        return 5
    if tier == DatingTier.plus.value:
        return 4
    return 3

# ==================== APP SETUP ====================

app = FastAPI(title="CliqUp API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/signup", response_model=TokenResponse, tags=["auth"])
async def signup(req: SignupRequest):
    if not req.email and not req.phone_e164:
        raise HTTPException(status_code=400, detail="Provide email or phone")
    
    # Check existing user
    if req.email:
        existing = await db.users.find_one({"email": req.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    if req.phone_e164:
        existing = await db.users.find_one({"phone_e164": req.phone_e164})
        if existing:
            raise HTTPException(status_code=400, detail="Phone already in use")
    
    # Check handle uniqueness
    existing_handle = await db.users.find_one({"handle": req.handle.lower()})
    if existing_handle:
        raise HTTPException(status_code=400, detail="Handle already taken")
    
    age_band = compute_age_band(req.dob)
    now = datetime.now(timezone.utc).isoformat()
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": req.email,
        "phone_e164": req.phone_e164,
        "password_hash": hash_password(req.password),
        "dob": req.dob,
        "age_band": age_band.value,
        "country_code": req.country_code,
        "status": UserStatus.active.value,
        "display_name": req.display_name,
        "handle": req.handle.lower(),
        "created_at": now,
        "updated_at": now,
    }
    
    await db.users.insert_one(user)
    
    # Create default profile
    profile = {
        "user_id": user_id,
        "handle": req.handle.lower(),
        "display_name": req.display_name,
        "bio": None,
        "avatar_url": None,
        "cover_url": None,
        "is_private": False,
        "dating_link_mode": DatingLinkMode.curated.value,
        "pronouns": None,
        "interests": [],
        "followers_count": 0,
        "following_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    await db.profiles.insert_one(profile)
    
    # Create entitlement
    entitlement = {
        "user_id": user_id,
        "no_feed_ads": False,
        "dating_tier": DatingTier.none.value,
        "squad_size_cap": 3,
        "created_at": now,
    }
    await db.entitlements.insert_one(entitlement)
    
    # Create meet access record
    meet_access = {
        "user_id": user_id,
        "age_assured_18plus": False,
        "meet_enabled": False,
        "photo_verified": False,
        "id_verified": False,
        "updated_at": now,
    }
    await db.meet_access.insert_one(meet_access)
    
    token = create_access_token({"sub": user_id, "age_band": age_band.value})
    
    user_response = {k: v for k, v in user.items() if k != "password_hash"}
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(req: LoginRequest):
    if not req.email and not req.phone_e164:
        raise HTTPException(status_code=400, detail="Provide email or phone")
    
    query = {}
    if req.email:
        query["email"] = req.email
    if req.phone_e164:
        query["phone_e164"] = req.phone_e164
    
    user = await db.users.find_one(query, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"], "age_band": user["age_band"]})
    
    user_response = {k: v for k, v in user.items() if k != "password_hash"}
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse, tags=["auth"])
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email"),
        phone_e164=current_user.get("phone_e164"),
        dob=current_user["dob"],
        age_band=current_user["age_band"],
        status=current_user["status"],
        display_name=current_user["display_name"],
        handle=current_user["handle"],
        created_at=current_user["created_at"],
    )

# ==================== PROFILE ROUTES ====================

@api_router.get("/profiles/me", response_model=ProfileResponse, tags=["profiles"])
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    profile = await db.profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse(**profile)

@api_router.put("/profiles/me", response_model=ProfileResponse, tags=["profiles"])
async def update_my_profile(req: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    
    if "handle" in update_data:
        update_data["handle"] = update_data["handle"].lower()
        existing = await db.profiles.find_one({
            "handle": update_data["handle"],
            "user_id": {"$ne": current_user["id"]}
        })
        if existing:
            raise HTTPException(status_code=400, detail="Handle already taken")
        # Also update user record
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"handle": update_data["handle"]}}
        )
    
    if "display_name" in update_data:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"display_name": update_data["display_name"]}}
        )
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.profiles.update_one(
        {"user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    profile = await db.profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    return ProfileResponse(**profile)

@api_router.get("/profiles/{user_id}", response_model=ProfileResponse, tags=["profiles"])
async def get_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse(**profile)

@api_router.get("/profiles/handle/{handle}", response_model=ProfileResponse, tags=["profiles"])
async def get_profile_by_handle(handle: str):
    profile = await db.profiles.find_one({"handle": handle.lower()}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse(**profile)

# ==================== FOLLOW SYSTEM ====================

@api_router.post("/profiles/{user_id}/follow", tags=["social"])
async def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = await db.follows.find_one({
        "follower_id": current_user["id"],
        "following_id": user_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already following")
    
    now = datetime.now(timezone.utc).isoformat()
    follow = {
        "id": str(uuid.uuid4()),
        "follower_id": current_user["id"],
        "following_id": user_id,
        "created_at": now,
    }
    await db.follows.insert_one(follow)
    
    # Update counts
    await db.profiles.update_one({"user_id": current_user["id"]}, {"$inc": {"following_count": 1}})
    await db.profiles.update_one({"user_id": user_id}, {"$inc": {"followers_count": 1}})
    
    # Create notification
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "follow",
        "title": "New Follower",
        "body": f"{current_user['display_name']} started following you",
        "data": {"follower_id": current_user["id"]},
        "read": False,
        "created_at": now,
    }
    await db.notifications.insert_one(notification)
    
    return {"ok": True}

@api_router.delete("/profiles/{user_id}/follow", tags=["social"])
async def unfollow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.follows.delete_one({
        "follower_id": current_user["id"],
        "following_id": user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Not following")
    
    await db.profiles.update_one({"user_id": current_user["id"]}, {"$inc": {"following_count": -1}})
    await db.profiles.update_one({"user_id": user_id}, {"$inc": {"followers_count": -1}})
    
    return {"ok": True}

@api_router.get("/profiles/{user_id}/followers", tags=["social"])
async def get_followers(user_id: str, limit: int = 50, current_user: dict = Depends(get_current_user)):
    follows = await db.follows.find({"following_id": user_id}, {"_id": 0}).limit(limit).to_list(limit)
    follower_ids = [f["follower_id"] for f in follows]
    profiles = await db.profiles.find({"user_id": {"$in": follower_ids}}, {"_id": 0}).to_list(limit)
    return profiles

@api_router.get("/profiles/{user_id}/following", tags=["social"])
async def get_following(user_id: str, limit: int = 50, current_user: dict = Depends(get_current_user)):
    follows = await db.follows.find({"follower_id": user_id}, {"_id": 0}).limit(limit).to_list(limit)
    following_ids = [f["following_id"] for f in follows]
    profiles = await db.profiles.find({"user_id": {"$in": following_ids}}, {"_id": 0}).to_list(limit)
    return profiles

# ==================== MEET (DATING) ROUTES ====================

@api_router.get("/meet/status", response_model=MeetStatusResponse, tags=["meet"])
async def get_meet_status(current_user: dict = Depends(get_current_user)):
    meet_access = await db.meet_access.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    if current_user["age_band"] != AgeBand.adult.value:
        return MeetStatusResponse(
            meet_locked=True,
            reason="Meet is only available for users 18+",
            age_assured_18plus=False,
            meet_enabled=False
        )
    
    if not meet_access or not meet_access.get("age_assured_18plus"):
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
        meet_enabled=meet_access.get("meet_enabled", False)
    )

@api_router.post("/meet/age-assure", tags=["meet"])
async def age_assure(current_user: dict = Depends(get_current_user)):
    if current_user["age_band"] != AgeBand.adult.value:
        raise HTTPException(status_code=403, detail="Meet is only available for users 18+")
    
    now = datetime.now(timezone.utc).isoformat()
    await db.meet_access.update_one(
        {"user_id": current_user["id"]},
        {"$set": {
            "age_assured_18plus": True,
            "meet_enabled": True,
            "updated_at": now
        }}
    )
    
    return {"age_assured_18plus": True, "meet_enabled": True}

# Dating Profile
@api_router.post("/meet/dating-profile", response_model=DatingProfileResponse, tags=["meet"])
async def create_dating_profile(req: DatingProfileRequest, current_user: dict = Depends(get_current_user)):
    # Check meet access
    meet_status = await get_meet_status(current_user)
    if meet_status.meet_locked:
        raise HTTPException(status_code=403, detail=meet_status.reason)
    
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.dating_profiles.find_one({"user_id": current_user["id"]})
    
    profile_data = {
        "user_id": current_user["id"],
        "intent": req.intent,
        "bio": req.bio,
        "prompts": req.prompts or [],
        "photos": req.photos or [],
        "preferences": req.preferences or {},
        "photo_verified": False,
        "id_verified": False,
        "updated_at": now,
    }
    
    if existing:
        await db.dating_profiles.update_one(
            {"user_id": current_user["id"]},
            {"$set": profile_data}
        )
    else:
        profile_data["created_at"] = now
        await db.dating_profiles.insert_one(profile_data)
    
    profile = await db.dating_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    return DatingProfileResponse(**profile)

@api_router.get("/meet/dating-profile", response_model=DatingProfileResponse, tags=["meet"])
async def get_my_dating_profile(current_user: dict = Depends(get_current_user)):
    profile = await db.dating_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Dating profile not found")
    return DatingProfileResponse(**profile)

@api_router.get("/meet/dating-profile/{user_id}", response_model=DatingProfileResponse, tags=["meet"])
async def get_dating_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    profile = await db.dating_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Dating profile not found")
    return DatingProfileResponse(**profile)

# ==================== SQUAD ROUTES ====================

@api_router.post("/meet/squads", response_model=SquadResponse, tags=["squads"])
async def create_squad(req: SquadCreateRequest, current_user: dict = Depends(get_current_user)):
    meet_status = await get_meet_status(current_user)
    if meet_status.meet_locked:
        raise HTTPException(status_code=403, detail=meet_status.reason)
    
    now = datetime.now(timezone.utc).isoformat()
    squad_id = str(uuid.uuid4())
    
    squad = {
        "id": squad_id,
        "owner_id": current_user["id"],
        "name": req.name,
        "visibility": req.visibility,
        "veto_enabled": req.veto_enabled,
        "created_at": now,
        "updated_at": now,
    }
    await db.squads.insert_one(squad)
    
    # Add owner as member
    member = {
        "id": str(uuid.uuid4()),
        "squad_id": squad_id,
        "user_id": current_user["id"],
        "role": SquadMemberRole.owner.value,
        "joined_at": now,
    }
    await db.squad_members.insert_one(member)
    
    profile = await db.profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    return SquadResponse(
        id=squad_id,
        owner_id=current_user["id"],
        name=req.name,
        visibility=req.visibility,
        veto_enabled=req.veto_enabled,
        member_count=1,
        members=[{
            "user_id": current_user["id"],
            "display_name": current_user["display_name"],
            "avatar_url": profile.get("avatar_url") if profile else None,
            "role": SquadMemberRole.owner.value
        }],
        created_at=now
    )

@api_router.get("/meet/squads", response_model=List[SquadResponse], tags=["squads"])
async def get_my_squads(current_user: dict = Depends(get_current_user)):
    memberships = await db.squad_members.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    squad_ids = [m["squad_id"] for m in memberships]
    
    squads = await db.squads.find({"id": {"$in": squad_ids}}, {"_id": 0}).to_list(100)
    
    result = []
    for squad in squads:
        members = await db.squad_members.find({"squad_id": squad["id"]}, {"_id": 0}).to_list(10)
        member_details = []
        for m in members:
            profile = await db.profiles.find_one({"user_id": m["user_id"]}, {"_id": 0})
            user = await db.users.find_one({"id": m["user_id"]}, {"_id": 0})
            if profile and user:
                member_details.append({
                    "user_id": m["user_id"],
                    "display_name": user.get("display_name"),
                    "avatar_url": profile.get("avatar_url"),
                    "role": m["role"]
                })
        
        result.append(SquadResponse(
            id=squad["id"],
            owner_id=squad["owner_id"],
            name=squad["name"],
            visibility=squad["visibility"],
            veto_enabled=squad["veto_enabled"],
            member_count=len(members),
            members=member_details,
            created_at=squad["created_at"]
        ))
    
    return result

@api_router.get("/meet/squads/{squad_id}", response_model=SquadResponse, tags=["squads"])
async def get_squad(squad_id: str, current_user: dict = Depends(get_current_user)):
    squad = await db.squads.find_one({"id": squad_id}, {"_id": 0})
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    
    members = await db.squad_members.find({"squad_id": squad_id}, {"_id": 0}).to_list(10)
    member_details = []
    for m in members:
        profile = await db.profiles.find_one({"user_id": m["user_id"]}, {"_id": 0})
        user = await db.users.find_one({"id": m["user_id"]}, {"_id": 0})
        if profile and user:
            member_details.append({
                "user_id": m["user_id"],
                "display_name": user.get("display_name"),
                "avatar_url": profile.get("avatar_url"),
                "role": m["role"]
            })
    
    return SquadResponse(
        id=squad["id"],
        owner_id=squad["owner_id"],
        name=squad["name"],
        visibility=squad["visibility"],
        veto_enabled=squad["veto_enabled"],
        member_count=len(members),
        members=member_details,
        created_at=squad["created_at"]
    )

@api_router.post("/meet/squads/{squad_id}/invite", response_model=SquadInviteResponse, tags=["squads"])
async def invite_to_squad(squad_id: str, req: SquadInviteRequest, current_user: dict = Depends(get_current_user)):
    squad = await db.squads.find_one({"id": squad_id}, {"_id": 0})
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    
    if squad["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only squad owner can invite")
    
    # Check cap
    entitlement = await db.entitlements.find_one({"user_id": current_user["id"]}, {"_id": 0})
    cap = get_squad_cap(entitlement.get("dating_tier", "none") if entitlement else "none")
    member_count = await db.squad_members.count_documents({"squad_id": squad_id})
    
    if member_count >= cap:
        raise HTTPException(status_code=403, detail=f"Squad is full (cap={cap})")
    
    # Check if already invited or member
    existing_invite = await db.squad_invites.find_one({
        "squad_id": squad_id,
        "invitee_id": req.invitee_id,
        "status": InviteStatus.pending.value
    })
    if existing_invite:
        raise HTTPException(status_code=400, detail="Already invited")
    
    existing_member = await db.squad_members.find_one({
        "squad_id": squad_id,
        "user_id": req.invitee_id
    })
    if existing_member:
        raise HTTPException(status_code=400, detail="Already a member")
    
    now = datetime.now(timezone.utc).isoformat()
    invite_id = str(uuid.uuid4())
    
    invite = {
        "id": invite_id,
        "squad_id": squad_id,
        "inviter_id": current_user["id"],
        "invitee_id": req.invitee_id,
        "status": InviteStatus.pending.value,
        "created_at": now,
        "updated_at": now,
    }
    await db.squad_invites.insert_one(invite)
    
    # Create notification
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": req.invitee_id,
        "type": "squad_invite",
        "title": "Squad Invite",
        "body": f"{current_user['display_name']} invited you to join {squad['name']}",
        "data": {"squad_id": squad_id, "invite_id": invite_id},
        "read": False,
        "created_at": now,
    }
    await db.notifications.insert_one(notification)
    
    return SquadInviteResponse(
        id=invite_id,
        squad_id=squad_id,
        squad_name=squad["name"],
        inviter_id=current_user["id"],
        inviter_name=current_user["display_name"],
        invitee_id=req.invitee_id,
        status=InviteStatus.pending.value,
        created_at=now
    )

@api_router.get("/meet/invites", response_model=List[SquadInviteResponse], tags=["squads"])
async def get_my_invites(current_user: dict = Depends(get_current_user)):
    invites = await db.squad_invites.find({
        "invitee_id": current_user["id"],
        "status": InviteStatus.pending.value
    }, {"_id": 0}).to_list(100)
    
    result = []
    for invite in invites:
        squad = await db.squads.find_one({"id": invite["squad_id"]}, {"_id": 0})
        inviter = await db.users.find_one({"id": invite["inviter_id"]}, {"_id": 0})
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

@api_router.post("/meet/squads/{squad_id}/invite/{invite_id}/accept", tags=["squads"])
async def accept_invite(squad_id: str, invite_id: str, current_user: dict = Depends(get_current_user)):
    invite = await db.squad_invites.find_one({"id": invite_id, "squad_id": squad_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    if invite["invitee_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your invite")
    
    meet_status = await get_meet_status(current_user)
    if meet_status.meet_locked:
        raise HTTPException(status_code=403, detail=meet_status.reason)
    
    # Check cap
    squad = await db.squads.find_one({"id": squad_id}, {"_id": 0})
    entitlement = await db.entitlements.find_one({"user_id": squad["owner_id"]}, {"_id": 0})
    cap = get_squad_cap(entitlement.get("dating_tier", "none") if entitlement else "none")
    member_count = await db.squad_members.count_documents({"squad_id": squad_id})
    
    if member_count >= cap:
        raise HTTPException(status_code=403, detail=f"Squad is full (cap={cap})")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update invite
    await db.squad_invites.update_one(
        {"id": invite_id},
        {"$set": {"status": InviteStatus.accepted.value, "updated_at": now}}
    )
    
    # Add as member
    member = {
        "id": str(uuid.uuid4()),
        "squad_id": squad_id,
        "user_id": current_user["id"],
        "role": SquadMemberRole.member.value,
        "joined_at": now,
    }
    await db.squad_members.insert_one(member)
    
    return {"ok": True, "squad_id": squad_id, "user_id": current_user["id"], "role": SquadMemberRole.member.value}

@api_router.post("/meet/squads/{squad_id}/invite/{invite_id}/decline", tags=["squads"])
async def decline_invite(squad_id: str, invite_id: str, current_user: dict = Depends(get_current_user)):
    invite = await db.squad_invites.find_one({"id": invite_id, "squad_id": squad_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    if invite["invitee_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your invite")
    
    now = datetime.now(timezone.utc).isoformat()
    await db.squad_invites.update_one(
        {"id": invite_id},
        {"$set": {"status": InviteStatus.declined.value, "updated_at": now}}
    )
    
    return {"ok": True}

# ==================== SWIPE & VOTE ====================

@api_router.get("/meet/discover", tags=["squads"])
async def discover_squads(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get squads to swipe on"""
    meet_status = await get_meet_status(current_user)
    if meet_status.meet_locked:
        raise HTTPException(status_code=403, detail=meet_status.reason)
    
    # Get user's squads
    my_memberships = await db.squad_members.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    my_squad_ids = [m["squad_id"] for m in my_memberships]
    
    # Get squads already swiped
    swiped = await db.squad_swipes.find({"squad_id": {"$in": my_squad_ids}}, {"_id": 0}).to_list(1000)
    swiped_target_ids = [s["target_squad_id"] for s in swiped]
    
    # Find other squads
    exclude_ids = my_squad_ids + swiped_target_ids
    squads = await db.squads.find(
        {"id": {"$nin": exclude_ids}},
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    result = []
    for squad in squads:
        members = await db.squad_members.find({"squad_id": squad["id"]}, {"_id": 0}).to_list(10)
        member_details = []
        for m in members:
            profile = await db.profiles.find_one({"user_id": m["user_id"]}, {"_id": 0})
            user = await db.users.find_one({"id": m["user_id"]}, {"_id": 0})
            dating_profile = await db.dating_profiles.find_one({"user_id": m["user_id"]}, {"_id": 0})
            if profile and user:
                member_details.append({
                    "user_id": m["user_id"],
                    "display_name": user.get("display_name"),
                    "avatar_url": profile.get("avatar_url"),
                    "bio": dating_profile.get("bio") if dating_profile else None,
                    "photos": dating_profile.get("photos", []) if dating_profile else [],
                })
        
        result.append({
            "id": squad["id"],
            "name": squad["name"],
            "member_count": len(members),
            "members": member_details,
        })
    
    return result

@api_router.post("/meet/squads/{squad_id}/swipe", response_model=SwipeResponse, tags=["squads"])
async def swipe_on_squad(squad_id: str, req: SwipeRequest, current_user: dict = Depends(get_current_user)):
    meet_status = await get_meet_status(current_user)
    if meet_status.meet_locked:
        raise HTTPException(status_code=403, detail=meet_status.reason)
    
    # Check membership
    membership = await db.squad_members.find_one({
        "squad_id": squad_id,
        "user_id": current_user["id"]
    })
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this squad")
    
    if squad_id == req.target_squad_id:
        raise HTTPException(status_code=400, detail="Cannot swipe on same squad")
    
    # Check if already swiped
    existing = await db.squad_swipes.find_one({
        "squad_id": squad_id,
        "target_squad_id": req.target_squad_id
    })
    if existing:
        return SwipeResponse(
            id=existing["id"],
            squad_id=existing["squad_id"],
            target_squad_id=existing["target_squad_id"],
            direction=existing["direction"],
            outcome=existing["outcome"]
        )
    
    now = datetime.now(timezone.utc).isoformat()
    swipe_id = str(uuid.uuid4())
    
    swipe = {
        "id": swipe_id,
        "squad_id": squad_id,
        "target_squad_id": req.target_squad_id,
        "direction": req.direction,
        "outcome": SwipeOutcome.pending.value,
        "created_at": now,
    }
    await db.squad_swipes.insert_one(swipe)
    
    return SwipeResponse(
        id=swipe_id,
        squad_id=squad_id,
        target_squad_id=req.target_squad_id,
        direction=req.direction,
        outcome=SwipeOutcome.pending.value
    )

@api_router.post("/meet/swipes/{swipe_id}/vote", response_model=VoteResponse, tags=["squads"])
async def vote_on_swipe(swipe_id: str, req: VoteRequest, current_user: dict = Depends(get_current_user)):
    swipe = await db.squad_swipes.find_one({"id": swipe_id}, {"_id": 0})
    if not swipe:
        raise HTTPException(status_code=404, detail="Swipe not found")
    
    meet_status = await get_meet_status(current_user)
    if meet_status.meet_locked:
        raise HTTPException(status_code=403, detail=meet_status.reason)
    
    # Check membership
    membership = await db.squad_members.find_one({
        "squad_id": swipe["squad_id"],
        "user_id": current_user["id"]
    })
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of the swiping squad")
    
    squad = await db.squads.find_one({"id": swipe["squad_id"]}, {"_id": 0})
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Upsert vote
    existing_vote = await db.squad_swipe_votes.find_one({
        "swipe_id": swipe_id,
        "voter_user_id": current_user["id"]
    })
    
    if existing_vote:
        await db.squad_swipe_votes.update_one(
            {"id": existing_vote["id"]},
            {"$set": {"vote": req.vote, "updated_at": now}}
        )
    else:
        vote = {
            "id": str(uuid.uuid4()),
            "swipe_id": swipe_id,
            "voter_user_id": current_user["id"],
            "vote": req.vote,
            "created_at": now,
        }
        await db.squad_swipe_votes.insert_one(vote)
    
    # Tally votes
    like_count = await db.squad_swipe_votes.count_documents({"swipe_id": swipe_id, "vote": VoteType.like.value})
    pass_count = await db.squad_swipe_votes.count_documents({"swipe_id": swipe_id, "vote": VoteType.pass_.value})
    veto_count = await db.squad_swipe_votes.count_documents({"swipe_id": swipe_id, "vote": VoteType.veto.value})
    
    member_count = await db.squad_members.count_documents({"squad_id": swipe["squad_id"]})
    required = get_required_likes(member_count)
    
    # Determine outcome
    outcome = SwipeOutcome.pending.value
    if squad and squad.get("veto_enabled") and veto_count > 0:
        outcome = SwipeOutcome.vetoed.value
    elif like_count >= required and swipe["direction"] == SwipeDirection.like.value:
        outcome = SwipeOutcome.liked.value
    elif pass_count >= required or swipe["direction"] == SwipeDirection.pass_.value:
        outcome = SwipeOutcome.passed.value
    
    await db.squad_swipes.update_one({"id": swipe_id}, {"$set": {"outcome": outcome}})
    
    # Check for match
    match_created = False
    match_id = None
    
    if outcome == SwipeOutcome.liked.value:
        # Check reciprocal
        reciprocal = await db.squad_swipes.find_one({
            "squad_id": swipe["target_squad_id"],
            "target_squad_id": swipe["squad_id"],
            "outcome": SwipeOutcome.liked.value
        })
        
        if reciprocal:
            # Create match
            a, b = (swipe["squad_id"], swipe["target_squad_id"]) if swipe["squad_id"] < swipe["target_squad_id"] else (swipe["target_squad_id"], swipe["squad_id"])
            
            existing_match = await db.squad_matches.find_one({
                "squad_a_id": a,
                "squad_b_id": b
            })
            
            if not existing_match:
                # Get all members
                members_a = await db.squad_members.find({"squad_id": a}, {"_id": 0}).to_list(10)
                members_b = await db.squad_members.find({"squad_id": b}, {"_id": 0}).to_list(10)
                member_ids = [m["user_id"] for m in members_a] + [m["user_id"] for m in members_b]
                
                # Create conversation
                conv_id = str(uuid.uuid4())
                conversation = {
                    "id": conv_id,
                    "type": ConversationType.meet_group.value,
                    "name": None,
                    "created_by": current_user["id"],
                    "created_at": now,
                    "updated_at": now,
                }
                await db.conversations.insert_one(conversation)
                
                # Add members
                for uid in set(member_ids):
                    await db.conversation_members.insert_one({
                        "id": str(uuid.uuid4()),
                        "conversation_id": conv_id,
                        "user_id": uid,
                        "joined_at": now,
                    })
                
                # Create match
                match_id = str(uuid.uuid4())
                match = {
                    "id": match_id,
                    "squad_a_id": a,
                    "squad_b_id": b,
                    "conversation_id": conv_id,
                    "matched_at": now,
                }
                await db.squad_matches.insert_one(match)
                match_created = True
                
                # Create notifications
                squad_a = await db.squads.find_one({"id": a}, {"_id": 0})
                squad_b = await db.squads.find_one({"id": b}, {"_id": 0})
                for uid in set(member_ids):
                    notification = {
                        "id": str(uuid.uuid4()),
                        "user_id": uid,
                        "type": "match",
                        "title": "New Match!",
                        "body": f"{squad_a['name']} and {squad_b['name']} matched!",
                        "data": {"match_id": match_id, "conversation_id": conv_id},
                        "read": False,
                        "created_at": now,
                    }
                    await db.notifications.insert_one(notification)
    
    return VoteResponse(
        swipe_id=swipe_id,
        voter_user_id=current_user["id"],
        vote=req.vote,
        outcome=outcome,
        like_count=like_count,
        pass_count=pass_count,
        veto_count=veto_count,
        required_likes=required,
        match_created=match_created,
        match_id=match_id
    )

@api_router.get("/meet/matches", response_model=List[MatchResponse], tags=["squads"])
async def get_matches(current_user: dict = Depends(get_current_user)):
    # Get user's squads
    memberships = await db.squad_members.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    squad_ids = [m["squad_id"] for m in memberships]
    
    if not squad_ids:
        return []
    
    matches = await db.squad_matches.find({
        "$or": [
            {"squad_a_id": {"$in": squad_ids}},
            {"squad_b_id": {"$in": squad_ids}}
        ]
    }, {"_id": 0}).to_list(100)
    
    result = []
    for match in matches:
        squad_a = await db.squads.find_one({"id": match["squad_a_id"]}, {"_id": 0})
        squad_b = await db.squads.find_one({"id": match["squad_b_id"]}, {"_id": 0})
        
        # Get all members
        members_a = await db.squad_members.find({"squad_id": match["squad_a_id"]}, {"_id": 0}).to_list(10)
        members_b = await db.squad_members.find({"squad_id": match["squad_b_id"]}, {"_id": 0}).to_list(10)
        
        member_details = []
        for m in members_a + members_b:
            profile = await db.profiles.find_one({"user_id": m["user_id"]}, {"_id": 0})
            user = await db.users.find_one({"id": m["user_id"]}, {"_id": 0})
            if profile and user:
                member_details.append({
                    "user_id": m["user_id"],
                    "display_name": user.get("display_name"),
                    "avatar_url": profile.get("avatar_url"),
                    "squad_id": m["squad_id"]
                })
        
        result.append(MatchResponse(
            id=match["id"],
            squad_a_id=match["squad_a_id"],
            squad_b_id=match["squad_b_id"],
            squad_a_name=squad_a["name"] if squad_a else "Unknown",
            squad_b_name=squad_b["name"] if squad_b else "Unknown",
            conversation_id=match["conversation_id"],
            matched_at=match["matched_at"],
            members=member_details
        ))
    
    return result

# ==================== MESSAGING ROUTES ====================

@api_router.get("/conversations", response_model=List[ConversationResponse], tags=["messaging"])
async def get_conversations(current_user: dict = Depends(get_current_user)):
    memberships = await db.conversation_members.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    conv_ids = [m["conversation_id"] for m in memberships]
    
    if not conv_ids:
        return []
    
    conversations = await db.conversations.find({"id": {"$in": conv_ids}}, {"_id": 0}).to_list(100)
    
    result = []
    for conv in conversations:
        members = await db.conversation_members.find({"conversation_id": conv["id"]}, {"_id": 0}).to_list(20)
        member_details = []
        for m in members:
            profile = await db.profiles.find_one({"user_id": m["user_id"]}, {"_id": 0})
            user = await db.users.find_one({"id": m["user_id"]}, {"_id": 0})
            if profile and user:
                member_details.append({
                    "user_id": m["user_id"],
                    "display_name": user.get("display_name"),
                    "avatar_url": profile.get("avatar_url"),
                })
        
        # Get last message
        last_msg = await db.messages.find_one(
            {"conversation_id": conv["id"]},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        
        result.append(ConversationResponse(
            id=conv["id"],
            type=conv["type"],
            name=conv.get("name"),
            created_by=conv["created_by"],
            members=member_details,
            last_message=last_msg,
            created_at=conv["created_at"],
            updated_at=conv.get("updated_at", conv["created_at"])
        ))
    
    # Sort by updated_at
    result.sort(key=lambda x: x.updated_at, reverse=True)
    return result

@api_router.get("/conversations/{conversation_id}", response_model=ConversationResponse, tags=["messaging"])
async def get_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    membership = await db.conversation_members.find_one({
        "conversation_id": conversation_id,
        "user_id": current_user["id"]
    })
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")
    
    conv = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    members = await db.conversation_members.find({"conversation_id": conversation_id}, {"_id": 0}).to_list(20)
    member_details = []
    for m in members:
        profile = await db.profiles.find_one({"user_id": m["user_id"]}, {"_id": 0})
        user = await db.users.find_one({"id": m["user_id"]}, {"_id": 0})
        if profile and user:
            member_details.append({
                "user_id": m["user_id"],
                "display_name": user.get("display_name"),
                "avatar_url": profile.get("avatar_url"),
            })
    
    last_msg = await db.messages.find_one(
        {"conversation_id": conversation_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    return ConversationResponse(
        id=conv["id"],
        type=conv["type"],
        name=conv.get("name"),
        created_by=conv["created_by"],
        members=member_details,
        last_message=last_msg,
        created_at=conv["created_at"],
        updated_at=conv.get("updated_at", conv["created_at"])
    )

@api_router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse], tags=["messaging"])
async def get_messages(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    membership = await db.conversation_members.find_one({
        "conversation_id": conversation_id,
        "user_id": current_user["id"]
    })
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")
    
    messages = await db.messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for msg in reversed(messages):
        profile = await db.profiles.find_one({"user_id": msg["sender_id"]}, {"_id": 0})
        user = await db.users.find_one({"id": msg["sender_id"]}, {"_id": 0})
        result.append(MessageResponse(
            id=msg["id"],
            conversation_id=msg["conversation_id"],
            sender_id=msg["sender_id"],
            sender_name=user.get("display_name", "Unknown") if user else "Unknown",
            sender_avatar=profile.get("avatar_url") if profile else None,
            body=msg["body"],
            created_at=msg["created_at"]
        ))
    
    return result

@api_router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, tags=["messaging"])
async def send_message(
    conversation_id: str,
    req: MessageRequest,
    current_user: dict = Depends(get_current_user)
):
    membership = await db.conversation_members.find_one({
        "conversation_id": conversation_id,
        "user_id": current_user["id"]
    })
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")
    
    now = datetime.now(timezone.utc).isoformat()
    msg_id = str(uuid.uuid4())
    
    message = {
        "id": msg_id,
        "conversation_id": conversation_id,
        "sender_id": current_user["id"],
        "body": req.body,
        "created_at": now,
    }
    await db.messages.insert_one(message)
    
    # Update conversation
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"updated_at": now}}
    )
    
    profile = await db.profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    return MessageResponse(
        id=msg_id,
        conversation_id=conversation_id,
        sender_id=current_user["id"],
        sender_name=current_user["display_name"],
        sender_avatar=profile.get("avatar_url") if profile else None,
        body=req.body,
        created_at=now
    )

# Create DM
@api_router.post("/conversations/dm/{user_id}", response_model=ConversationResponse, tags=["messaging"])
async def create_dm(user_id: str, current_user: dict = Depends(get_current_user)):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot DM yourself")
    
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check existing DM
    my_convs = await db.conversation_members.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    my_conv_ids = [c["conversation_id"] for c in my_convs]
    
    for conv_id in my_conv_ids:
        conv = await db.conversations.find_one({"id": conv_id, "type": ConversationType.dm.value}, {"_id": 0})
        if conv:
            other_member = await db.conversation_members.find_one({
                "conversation_id": conv_id,
                "user_id": user_id
            })
            if other_member:
                # Return existing
                members = await db.conversation_members.find({"conversation_id": conv_id}, {"_id": 0}).to_list(2)
                member_details = []
                for m in members:
                    profile = await db.profiles.find_one({"user_id": m["user_id"]}, {"_id": 0})
                    u = await db.users.find_one({"id": m["user_id"]}, {"_id": 0})
                    if profile and u:
                        member_details.append({
                            "user_id": m["user_id"],
                            "display_name": u.get("display_name"),
                            "avatar_url": profile.get("avatar_url"),
                        })
                return ConversationResponse(
                    id=conv["id"],
                    type=conv["type"],
                    name=conv.get("name"),
                    created_by=conv["created_by"],
                    members=member_details,
                    last_message=None,
                    created_at=conv["created_at"],
                    updated_at=conv.get("updated_at", conv["created_at"])
                )
    
    # Create new DM
    now = datetime.now(timezone.utc).isoformat()
    conv_id = str(uuid.uuid4())
    
    conversation = {
        "id": conv_id,
        "type": ConversationType.dm.value,
        "name": None,
        "created_by": current_user["id"],
        "created_at": now,
        "updated_at": now,
    }
    await db.conversations.insert_one(conversation)
    
    for uid in [current_user["id"], user_id]:
        await db.conversation_members.insert_one({
            "id": str(uuid.uuid4()),
            "conversation_id": conv_id,
            "user_id": uid,
            "joined_at": now,
        })
    
    members = []
    for uid in [current_user["id"], user_id]:
        profile = await db.profiles.find_one({"user_id": uid}, {"_id": 0})
        u = await db.users.find_one({"id": uid}, {"_id": 0})
        if profile and u:
            members.append({
                "user_id": uid,
                "display_name": u.get("display_name"),
                "avatar_url": profile.get("avatar_url"),
            })
    
    return ConversationResponse(
        id=conv_id,
        type=ConversationType.dm.value,
        name=None,
        created_by=current_user["id"],
        members=members,
        last_message=None,
        created_at=now,
        updated_at=now
    )

# ==================== POSTS (FEED) ROUTES ====================

@api_router.post("/posts", response_model=PostResponse, tags=["posts"])
async def create_post(req: PostCreateRequest, current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    post_id = str(uuid.uuid4())
    
    post = {
        "id": post_id,
        "user_id": current_user["id"],
        "type": req.type,
        "content": req.content,
        "media_urls": req.media_urls or [],
        "tags": req.tags or [],
        "reactions_count": 0,
        "comments_count": 0,
        "shares_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    await db.posts.insert_one(post)
    
    profile = await db.profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    return PostResponse(
        id=post_id,
        user_id=current_user["id"],
        user_name=current_user["display_name"],
        user_handle=current_user["handle"],
        user_avatar=profile.get("avatar_url") if profile else None,
        type=req.type,
        content=req.content,
        media_urls=req.media_urls or [],
        tags=req.tags or [],
        reactions_count=0,
        comments_count=0,
        shares_count=0,
        user_reaction=None,
        created_at=now
    )

@api_router.get("/posts/feed", response_model=List[PostResponse], tags=["posts"])
async def get_feed(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    # Get following
    following = await db.follows.find({"follower_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    following_ids = [f["following_id"] for f in following]
    following_ids.append(current_user["id"])  # Include own posts
    
    posts = await db.posts.find(
        {"user_id": {"$in": following_ids}},
        {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        user = await db.users.find_one({"id": post["user_id"]}, {"_id": 0})
        profile = await db.profiles.find_one({"user_id": post["user_id"]}, {"_id": 0})
        
        # Check user's reaction
        user_reaction = await db.post_reactions.find_one({
            "post_id": post["id"],
            "user_id": current_user["id"]
        }, {"_id": 0})
        
        result.append(PostResponse(
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
        ))
    
    return result

@api_router.get("/posts/explore", response_model=List[PostResponse], tags=["posts"])
async def get_explore(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get trending/recommended posts"""
    posts = await db.posts.find(
        {},
        {"_id": 0}
    ).sort("reactions_count", -1).skip(offset).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        user = await db.users.find_one({"id": post["user_id"]}, {"_id": 0})
        profile = await db.profiles.find_one({"user_id": post["user_id"]}, {"_id": 0})
        
        user_reaction = await db.post_reactions.find_one({
            "post_id": post["id"],
            "user_id": current_user["id"]
        }, {"_id": 0})
        
        result.append(PostResponse(
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
        ))
    
    return result

@api_router.get("/posts/{post_id}", response_model=PostResponse, tags=["posts"])
async def get_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = await db.posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user = await db.users.find_one({"id": post["user_id"]}, {"_id": 0})
    profile = await db.profiles.find_one({"user_id": post["user_id"]}, {"_id": 0})
    
    user_reaction = await db.post_reactions.find_one({
        "post_id": post_id,
        "user_id": current_user["id"]
    }, {"_id": 0})
    
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

@api_router.post("/posts/{post_id}/react", tags=["posts"])
async def react_to_post(post_id: str, req: ReactionRequest, current_user: dict = Depends(get_current_user)):
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    existing = await db.post_reactions.find_one({
        "post_id": post_id,
        "user_id": current_user["id"]
    })
    
    now = datetime.now(timezone.utc).isoformat()
    
    if existing:
        if existing["reaction_type"] == req.reaction_type:
            # Remove reaction
            await db.post_reactions.delete_one({"id": existing["id"]})
            await db.posts.update_one({"id": post_id}, {"$inc": {"reactions_count": -1}})
            return {"ok": True, "action": "removed"}
        else:
            # Update reaction
            await db.post_reactions.update_one(
                {"id": existing["id"]},
                {"$set": {"reaction_type": req.reaction_type, "updated_at": now}}
            )
            return {"ok": True, "action": "updated"}
    else:
        # Add reaction
        reaction = {
            "id": str(uuid.uuid4()),
            "post_id": post_id,
            "user_id": current_user["id"],
            "reaction_type": req.reaction_type,
            "created_at": now,
        }
        await db.post_reactions.insert_one(reaction)
        await db.posts.update_one({"id": post_id}, {"$inc": {"reactions_count": 1}})
        return {"ok": True, "action": "added"}

@api_router.post("/posts/{post_id}/comments", response_model=CommentResponse, tags=["posts"])
async def create_comment(post_id: str, req: CommentRequest, current_user: dict = Depends(get_current_user)):
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    now = datetime.now(timezone.utc).isoformat()
    comment_id = str(uuid.uuid4())
    
    comment = {
        "id": comment_id,
        "post_id": post_id,
        "user_id": current_user["id"],
        "content": req.content,
        "parent_id": req.parent_id,
        "replies_count": 0,
        "created_at": now,
    }
    await db.comments.insert_one(comment)
    
    await db.posts.update_one({"id": post_id}, {"$inc": {"comments_count": 1}})
    
    if req.parent_id:
        await db.comments.update_one({"id": req.parent_id}, {"$inc": {"replies_count": 1}})
    
    profile = await db.profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    return CommentResponse(
        id=comment_id,
        post_id=post_id,
        user_id=current_user["id"],
        user_name=current_user["display_name"],
        user_handle=current_user["handle"],
        user_avatar=profile.get("avatar_url") if profile else None,
        content=req.content,
        parent_id=req.parent_id,
        replies_count=0,
        created_at=now
    )

@api_router.get("/posts/{post_id}/comments", response_model=List[CommentResponse], tags=["posts"])
async def get_comments(
    post_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    comments = await db.comments.find(
        {"post_id": post_id, "parent_id": None},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for comment in comments:
        user = await db.users.find_one({"id": comment["user_id"]}, {"_id": 0})
        profile = await db.profiles.find_one({"user_id": comment["user_id"]}, {"_id": 0})
        
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

# ==================== STORIES ROUTES ====================

@api_router.post("/stories", response_model=StoryResponse, tags=["stories"])
async def create_story(req: StoryCreateRequest, current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)
    
    story_id = str(uuid.uuid4())
    story = {
        "id": story_id,
        "user_id": current_user["id"],
        "media_url": req.media_url,
        "media_type": req.media_type,
        "caption": req.caption,
        "duration": req.duration,
        "views_count": 0,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    await db.stories.insert_one(story)
    
    profile = await db.profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    
    return StoryResponse(
        id=story_id,
        user_id=current_user["id"],
        user_name=current_user["display_name"],
        user_handle=current_user["handle"],
        user_avatar=profile.get("avatar_url") if profile else None,
        media_url=req.media_url,
        media_type=req.media_type,
        caption=req.caption,
        duration=req.duration,
        views_count=0,
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat()
    )

@api_router.get("/stories/feed", response_model=List[dict], tags=["stories"])
async def get_stories_feed(current_user: dict = Depends(get_current_user)):
    """Get stories from followed users grouped by user"""
    following = await db.follows.find({"follower_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    following_ids = [f["following_id"] for f in following]
    following_ids.append(current_user["id"])
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Get active stories
    stories = await db.stories.find({
        "user_id": {"$in": following_ids},
        "expires_at": {"$gt": now}
    }, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Group by user
    user_stories = {}
    for story in stories:
        uid = story["user_id"]
        if uid not in user_stories:
            user = await db.users.find_one({"id": uid}, {"_id": 0})
            profile = await db.profiles.find_one({"user_id": uid}, {"_id": 0})
            user_stories[uid] = {
                "user_id": uid,
                "user_name": user.get("display_name") if user else "Unknown",
                "user_handle": user.get("handle") if user else "unknown",
                "user_avatar": profile.get("avatar_url") if profile else None,
                "stories": []
            }
        user_stories[uid]["stories"].append(story)
    
    return list(user_stories.values())

@api_router.post("/stories/{story_id}/view", tags=["stories"])
async def view_story(story_id: str, current_user: dict = Depends(get_current_user)):
    story = await db.stories.find_one({"id": story_id})
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Check if already viewed
    existing = await db.story_views.find_one({
        "story_id": story_id,
        "user_id": current_user["id"]
    })
    
    if not existing:
        now = datetime.now(timezone.utc).isoformat()
        await db.story_views.insert_one({
            "id": str(uuid.uuid4()),
            "story_id": story_id,
            "user_id": current_user["id"],
            "viewed_at": now,
        })
        await db.stories.update_one({"id": story_id}, {"$inc": {"views_count": 1}})
    
    return {"ok": True}

# ==================== NOTIFICATIONS ====================

@api_router.get("/notifications", response_model=List[NotificationResponse], tags=["notifications"])
async def get_notifications(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    notifications = await db.notifications.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [NotificationResponse(**n) for n in notifications]

@api_router.post("/notifications/{notification_id}/read", tags=["notifications"])
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user["id"]},
        {"$set": {"read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}

@api_router.post("/notifications/read-all", tags=["notifications"])
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    await db.notifications.update_many(
        {"user_id": current_user["id"], "read": False},
        {"$set": {"read": True}}
    )
    return {"ok": True}

@api_router.get("/notifications/unread-count", tags=["notifications"])
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    count = await db.notifications.count_documents({
        "user_id": current_user["id"],
        "read": False
    })
    return {"count": count}

# ==================== SEARCH ====================

@api_router.get("/search/users", tags=["search"])
async def search_users(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    # Search by handle or display_name
    users = await db.users.find({
        "$or": [
            {"handle": {"$regex": q, "$options": "i"}},
            {"display_name": {"$regex": q, "$options": "i"}}
        ]
    }, {"_id": 0, "password_hash": 0}).limit(limit).to_list(limit)
    
    result = []
    for user in users:
        profile = await db.profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        result.append({
            "id": user["id"],
            "handle": user["handle"],
            "display_name": user["display_name"],
            "avatar_url": profile.get("avatar_url") if profile else None,
            "bio": profile.get("bio") if profile else None,
        })
    
    return result

@api_router.get("/search/posts", tags=["search"])
async def search_posts(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    posts = await db.posts.find({
        "$or": [
            {"content": {"$regex": q, "$options": "i"}},
            {"tags": {"$in": [q.lower()]}}
        ]
    }, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        user = await db.users.find_one({"id": post["user_id"]}, {"_id": 0})
        profile = await db.profiles.find_one({"user_id": post["user_id"]}, {"_id": 0})
        result.append(PostResponse(
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
            user_reaction=None,
            created_at=post["created_at"]
        ))
    
    return result

# ==================== HEALTH & ROOT ====================

@api_router.get("/", tags=["system"])
async def root():
    return {"message": "CliqUp API", "version": "1.0.0"}

@api_router.get("/health", tags=["system"])
async def health():
    return {"ok": True, "status": "healthy"}

# ==================== APP CONFIG ====================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
