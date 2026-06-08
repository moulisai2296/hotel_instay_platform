"""Guest PIN authentication — business logic + the data-access seam.

Mobile-first flow (docs/FLOWS.md §2, adapted to phone-only): the hotel is known
from the URL slug, the guest types room number + 6-digit PIN, and on success we
mint a short-lived guest JWT that satisfies the InStayOS claims contract
(CLAUDE.md) so Step 3's ``get_context`` / hotel-isolation guard accept it.

Pure helpers here are DB-free and unit-testable; ``GuestAuthService`` wraps the
DB lookup/write and is the dependency tests override with a fake.
"""

import dataclasses
import uuid
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_auth_kit
from models import GuestSession, Hotel, Room

# A real bcrypt hash of a throwaway value. When no session matches, we still run
# one checkpw against this so a wrong room/hotel costs the same time as a wrong
# PIN — defeating timing-based enumeration of valid rooms.
_DUMMY_HASH = bcrypt.hashpw(b"timing-equalizer", bcrypt.gensalt()).decode("utf-8")


@dataclasses.dataclass(frozen=True)
class ResolvedSession:
    """An active guest session plus the room/hotel context needed to mint a token."""

    session: GuestSession
    room_number: str
    hotel_timezone: str | None


# --- Pure helpers ------------------------------------------------------------


def verify_pin(pin: str, pin_hash: str) -> bool:
    """Constant-time bcrypt comparison; never raises on a malformed hash."""
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), pin_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def burn_dummy_check(pin: str) -> None:
    """Run a throwaway bcrypt check to equalize timing when no session is found."""
    try:
        bcrypt.checkpw(pin.encode("utf-8"), _DUMMY_HASH.encode("utf-8"))
    except (ValueError, TypeError):
        pass


def is_session_active(session: GuestSession, today: date) -> bool:
    """Active = not checked out and today within [checkin, checkout]."""
    return (
        not session.is_checked_out
        and session.checkin_date <= today <= session.checkout_date
    )


def compute_token_expiry(checkout_date: date, hotel_timezone: str | None) -> datetime:
    """End of the checkout day (23:59:59) in the hotel's timezone, as UTC.

    The guest JWT lives until the guest is expected to have left. Falls back to
    UTC when the hotel has no/invalid timezone configured.
    """
    try:
        tz = ZoneInfo(hotel_timezone) if hotel_timezone else timezone.utc
    except (ZoneInfoNotFoundError, ValueError):
        tz = timezone.utc
    local_eod = datetime.combine(checkout_date, time(23, 59, 59), tzinfo=tz)
    return local_eod.astimezone(timezone.utc)


def build_guest_claims(
    session: GuestSession, room_number: str, expires_at: datetime
) -> dict:
    """Assemble the guest JWT payload per the InStayOS claims contract.

    ``type="access"`` is required so the Step 3 ``get_context`` dependency accepts
    the token. ``sub`` and ``session_id`` are both the guest_session id.
    """
    now = datetime.now(timezone.utc)
    return {
        "sub": str(session.id),
        "role": "authenticated",  # required by Supabase RLS
        "app_role": "guest",
        "hotel_id": str(session.hotel_id),
        "department_id": None,
        "session_id": str(session.id),
        "room_id": str(session.room_id),
        "room_number": room_number,
        "guest_name": session.guest_name,
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }


def mint_guest_token(claims: dict) -> str:
    """Sign the guest token with authkit's secret/algorithm (single source)."""
    config = get_auth_kit().config
    return jwt.encode(claims, config.secret_key, algorithm=config.algorithm)


# --- Data-access seam (overridden in tests) ----------------------------------


class GuestAuthService:
    """DB-backed guest session lookup + token bookkeeping."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_active_session(
        self, hotel_slug: str, room_number: str, today: date | None = None
    ) -> ResolvedSession | None:
        """Resolve the single active session for (hotel_slug, room_number).

        Returns None for unknown hotel/room or no active stay — the caller maps
        every None to the same generic 401, so this never reveals which part failed.
        """
        today = today or datetime.now(timezone.utc).date()
        stmt = (
            select(GuestSession, Hotel.timezone)
            .join(Hotel, Hotel.id == GuestSession.hotel_id)
            .join(Room, Room.id == GuestSession.room_id)
            .where(
                Hotel.slug == hotel_slug,
                Room.room_number == room_number,
                GuestSession.is_checked_out.is_(False),
                GuestSession.checkin_date <= today,
                GuestSession.checkout_date >= today,
            )
            .order_by(GuestSession.checkin_date.desc())
        )
        row = (await self.db.execute(stmt)).first()
        if row is None:
            return None
        session, hotel_timezone = row
        return ResolvedSession(
            session=session, room_number=room_number, hotel_timezone=hotel_timezone
        )

    async def record_token(
        self, session: GuestSession, token: str, expires_at: datetime
    ) -> None:
        """Persist token expiry + a SHA-256 hash of the token (never the raw token)."""
        session.session_token = get_auth_kit().auth_service.hash_token(token)
        session.token_expires_at = expires_at
        await self.db.commit()
