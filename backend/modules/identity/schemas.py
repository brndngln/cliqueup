"""
Identity module - Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


# ==================== Request Schemas ====================

class SignupRequest(BaseModel):
    """User registration request."""
    email: Optional[EmailStr] = None
    phone_e164: Optional[str] = None
    password: str = Field(min_length=8, description="Minimum 8 characters")
    dob: str = Field(description="Date of birth (YYYY-MM-DD)")
    country_code: Optional[str] = None
    display_name: str = Field(min_length=1, max_length=50)
    handle: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")


class LoginRequest(BaseModel):
    """User login request."""
    email: Optional[EmailStr] = None
    phone_e164: Optional[str] = None
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


# ==================== Response Schemas ====================

class UserResponse(BaseModel):
    """User data response (excludes sensitive fields)."""
    id: str
    email: Optional[str] = None
    phone_e164: Optional[str] = None
    dob: str
    age_band: str
    status: str
    display_name: str
    handle: str
    created_at: str
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class AuthStatusResponse(BaseModel):
    """Authentication status check response."""
    authenticated: bool
    user: Optional[UserResponse] = None
