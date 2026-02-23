"""
Modules package - All application modules.
"""
from .identity import router as identity_router
from .profiles import router as profiles_router
from .social import router as social_router
from .meet import router as meet_router
from .messaging import router as messaging_router

__all__ = [
    "identity_router",
    "profiles_router",
    "social_router",
    "meet_router",
    "messaging_router"
]
