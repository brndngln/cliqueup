"""
Utility helper functions.
"""
from datetime import datetime, date, timezone
import uuid


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Get current UTC datetime as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def compute_age(dob_str: str) -> int:
    """Compute age from date of birth string (YYYY-MM-DD)."""
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def compute_age_band(dob_str: str) -> str:
    """Compute age band from date of birth."""
    from core.enums import AgeBand
    age = compute_age(dob_str)
    if age < 13:
        return AgeBand.U13.value
    if age < 18:
        return AgeBand.TEEN.value
    return AgeBand.ADULT.value


def get_squad_cap(tier: str) -> int:
    """Get squad member cap based on tier."""
    from core.config import settings
    from core.enums import DatingTier
    
    if tier == DatingTier.ELITE.value:
        return settings.ELITE_SQUAD_CAP
    if tier == DatingTier.PLUS.value:
        return settings.PLUS_SQUAD_CAP
    return settings.FREE_SQUAD_CAP


def get_required_likes(member_count: int) -> int:
    """Calculate required likes for a swipe to pass."""
    if member_count <= 2:
        return 2
    if member_count == 3:
        return 2
    if member_count == 4:
        return 3
    return 3  # 5+
