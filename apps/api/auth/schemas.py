import uuid
from datetime import datetime
from typing import Optional

from authkit_fastapi.schemas import UserCreate, UserRead, UserUpdate

# =========================================================================
# InStayOS Pydantic schemas — extend authkit's base schemas with the staff
# fields that live on the `users` table / User model (display_name, hotel_id,
# department_id, avatar_url, last_seen_at).
# =========================================================================


class CustomUserCreate(UserCreate):
    """Payload for provisioning a staff member (admin panel)."""

    display_name: str
    hotel_id: Optional[uuid.UUID] = None      # NULL for super-admin
    department_id: Optional[uuid.UUID] = None  # NULL for managers/admin


class CustomUserRead(UserRead):
    """Staff profile returned by the API (e.g. /auth/me)."""

    display_name: str
    hotel_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    avatar_url: Optional[str] = None
    last_seen_at: Optional[datetime] = None


class CustomUserUpdate(UserUpdate):
    display_name: Optional[str] = None
    hotel_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    avatar_url: Optional[str] = None
