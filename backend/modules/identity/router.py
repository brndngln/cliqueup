"""
Identity module - API router for authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.database import Database
from ...core.security import get_current_user
from .schemas import (
    SignupRequest, 
    LoginRequest, 
    TokenResponse, 
    UserResponse
)
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service() -> AuthService:
    """Dependency injection for AuthService."""
    db = Database.get_db()
    return AuthService(db)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    
    - **email** or **phone_e164**: At least one required
    - **password**: Minimum 8 characters
    - **dob**: Date of birth (YYYY-MM-DD) for age verification
    - **handle**: Unique username (3-30 alphanumeric characters)
    """
    return await service.signup(request)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and obtain access token.
    
    Provide either **email** or **phone_e164** with **password**.
    """
    return await service.login(request)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    """
    Get current authenticated user's information.
    
    Requires valid Bearer token in Authorization header.
    """
    user = await service.get_current_user(current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify if the current token is valid.
    
    Returns user info if token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user["id"],
        "age_band": current_user["age_band"]
    }
