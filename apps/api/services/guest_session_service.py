"""Staff-side guest check-in: allocate a room + mint a PIN -> a guest_sessions row.

This is the manual path that replaces the dev seed script (and stands in until PMS
integration lands). The generated PIN is returned to the caller exactly once; only
its bcrypt hash is persisted. Hotel scope comes from the staff JWT context.
"""

import secrets
import uuid
from datetime import date

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from middleware import RequestContext
from models import GuestSession, Room


def generate_pin() -> str:
    """A random 6-digit numeric PIN (cryptographically sourced)."""
    return f"{secrets.randbelow(1_000_000):06d}"


class GuestSessionService:
    """Create guest stays for a hotel from the staff/manager surface."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        ctx: RequestContext,
        *,
        room_number: str,
        guest_name: str,
        checkout_date: date,
        checkin_date: date | None = None,
        num_guests: int = 1,
        guest_email: str | None = None,
        pin: str | None = None,
    ) -> tuple[GuestSession, str]:
        """Create the stay and return ``(session, plaintext_pin)``.

        The room is resolved by number within the manager's hotel; if it doesn't
        exist yet it's created (rooms are otherwise admin-configured / PMS-synced).
        """
        hotel_id = ctx.hotel_id
        room = await self.db.scalar(
            select(Room).where(
                Room.hotel_id == hotel_id, Room.room_number == room_number
            )
        )
        if room is None:
            room = Room(hotel_id=hotel_id, room_number=room_number)
            self.db.add(room)
            await self.db.flush()  # assign room.id

        plain_pin = pin or generate_pin()
        session = GuestSession(
            hotel_id=hotel_id,
            room_id=room.id,
            guest_name=guest_name,
            guest_email=guest_email,
            pin_hash=bcrypt.hashpw(plain_pin.encode(), bcrypt.gensalt()).decode(),
            checkin_date=checkin_date or date.today(),
            checkout_date=checkout_date,
            num_guests=num_guests,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session, plain_pin
