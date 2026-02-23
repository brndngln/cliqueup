"""
Identity module - Service layer for authentication business logic.
"""
from typing import Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.security import hash_password, verify_password, create_access_token
from core.config import settings
from core.enums import UserStatus, DatingTier, DatingLinkMode
from utils.helpers import generate_id, utc_now_iso, compute_age_band
from modules.identity.repository import UserRepository
from modules.identity.schemas import SignupRequest, LoginRequest, UserResponse, TokenResponse


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def signup(self, request: SignupRequest) -> TokenResponse:
        """Register a new user."""
        # Validate at least one identifier
        if not request.email and not request.phone_e164:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or phone number is required"
            )
        
        # Check for existing users
        if request.email and await self.user_repo.exists_by_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        if request.phone_e164 and await self.user_repo.exists_by_phone(request.phone_e164):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already in use"
            )
        
        if await self.user_repo.exists_by_handle(request.handle):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Handle already taken"
            )
        
        # Compute age band
        age_band = compute_age_band(request.dob)
        now = utc_now_iso()
        user_id = generate_id()
        
        # Create user record
        user_data = {
            "id": user_id,
            "email": request.email,
            "phone_e164": request.phone_e164,
            "password_hash": hash_password(request.password),
            "dob": request.dob,
            "age_band": age_band,
            "country_code": request.country_code,
            "status": UserStatus.ACTIVE.value,
            "display_name": request.display_name,
            "handle": request.handle.lower(),
            "elo_rating": settings.DEFAULT_ELO,
            "created_at": now,
            "updated_at": now,
        }
        
        await self.user_repo.create(user_data)
        
        # Create associated records
        await self._create_user_records(user_id, request, now)
        
        # Generate token
        token = create_access_token({
            "sub": user_id,
            "age_band": age_band
        })
        
        user_response = UserResponse(
            id=user_id,
            email=request.email,
            phone_e164=request.phone_e164,
            dob=request.dob,
            age_band=age_band,
            status=UserStatus.ACTIVE.value,
            display_name=request.display_name,
            handle=request.handle.lower(),
            created_at=now
        )
        
        return TokenResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    async def _create_user_records(
        self, 
        user_id: str, 
        request: SignupRequest, 
        timestamp: str
    ):
        """Create associated user records (profile, entitlements, meet access)."""
        from core.database import Collections
        
        # Profile
        profile = {
            "user_id": user_id,
            "handle": request.handle.lower(),
            "display_name": request.display_name,
            "bio": None,
            "avatar_url": None,
            "cover_url": None,
            "is_private": False,
            "dating_link_mode": DatingLinkMode.CURATED.value,
            "pronouns": None,
            "interests": [],
            "followers_count": 0,
            "following_count": 0,
            "posts_count": 0,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        await self.db[Collections.PROFILES].insert_one(profile)
        
        # Entitlements
        entitlement = {
            "user_id": user_id,
            "no_feed_ads": False,
            "dating_tier": DatingTier.NONE.value,
            "squad_size_cap": settings.FREE_SQUAD_CAP,
            "created_at": timestamp,
        }
        await self.db[Collections.ENTITLEMENTS].insert_one(entitlement)
        
        # Meet Access
        meet_access = {
            "user_id": user_id,
            "age_assured_18plus": False,
            "meet_enabled": False,
            "photo_verified": False,
            "id_verified": False,
            "updated_at": timestamp,
        }
        await self.db[Collections.MEET_ACCESS].insert_one(meet_access)
    
    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate user and return token."""
        if not request.email and not request.phone_e164:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or phone number is required"
            )
        
        user = await self.user_repo.find_by_email_or_phone(
            email=request.email,
            phone=request.phone_e164
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not verify_password(request.password, user.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if user.get("status") == UserStatus.BANNED.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been banned"
            )
        
        token = create_access_token({
            "sub": user["id"],
            "age_band": user["age_band"]
        })
        
        user_response = UserResponse(
            id=user["id"],
            email=user.get("email"),
            phone_e164=user.get("phone_e164"),
            dob=user["dob"],
            age_band=user["age_band"],
            status=user["status"],
            display_name=user["display_name"],
            handle=user["handle"],
            created_at=user["created_at"]
        )
        
        return TokenResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    async def get_current_user(self, user_id: str) -> Optional[UserResponse]:
        """Get current user data."""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return None
        
        return UserResponse(
            id=user["id"],
            email=user.get("email"),
            phone_e164=user.get("phone_e164"),
            dob=user["dob"],
            age_band=user["age_band"],
            status=user["status"],
            display_name=user["display_name"],
            handle=user["handle"],
            created_at=user["created_at"]
        )
