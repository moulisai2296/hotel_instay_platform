"""Dev-only: seed one active guest session in `smoke-test-hotel` so the guest
PIN flow can be tested end-to-end. Throwaway (like the staff smoke users) — not
for production. Idempotent: re-running reuses the same room + active session.

Run:  cd apps/api && uv run python scripts/seed_guest_session.py
"""

import asyncio
import os
import sys
from datetime import date, timedelta
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))  # make `auth`, `models` importable

# 1. Load apps/api/.env into the environment BEFORE importing the DB engine.
ENV_PATH = API_ROOT / ".env"
for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, _, value = line.partition("=")
    os.environ.setdefault(key.strip(), value.strip())

import bcrypt  # noqa: E402
from sqlalchemy import select  # noqa: E402

from auth.setup import get_sessionmaker  # noqa: E402
from models import GuestSession, Hotel, Room  # noqa: E402

HOTEL_SLUG = "smoke-test-hotel"
ROOM_NUMBER = "101"
PIN = "123456"
GUEST_NAME = "Sam Lee"


async def main() -> None:
    today = date.today()
    async with get_sessionmaker()() as db:
        hotel = (
            await db.execute(select(Hotel).where(Hotel.slug == HOTEL_SLUG))
        ).scalar_one_or_none()
        if hotel is None:
            raise SystemExit(
                f"Hotel '{HOTEL_SLUG}' not found — seed the staff users first."
            )

        # Reuse the room if it exists, else create it.
        room = (
            await db.execute(
                select(Room).where(
                    Room.hotel_id == hotel.id, Room.room_number == ROOM_NUMBER
                )
            )
        ).scalar_one_or_none()
        if room is None:
            room = Room(
                hotel_id=hotel.id, room_number=ROOM_NUMBER, room_type="Deluxe", floor=1
            )
            db.add(room)
            await db.flush()

        # Skip if an active session already covers today for this room.
        existing = (
            await db.execute(
                select(GuestSession).where(
                    GuestSession.room_id == room.id,
                    GuestSession.is_checked_out.is_(False),
                    GuestSession.checkin_date <= today,
                    GuestSession.checkout_date >= today,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            print(
                f"Active session already exists (id={existing.id}). "
                f"Login: hotel='{HOTEL_SLUG}', room='{ROOM_NUMBER}', PIN='{PIN}' "
                "(only if it was seeded with this PIN)."
            )
            return

        session = GuestSession(
            hotel_id=hotel.id,
            room_id=room.id,
            guest_name=GUEST_NAME,
            pin_hash=bcrypt.hashpw(PIN.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
            checkin_date=today - timedelta(days=1),
            checkout_date=today + timedelta(days=3),
            num_guests=2,
        )
        db.add(session)
        await db.commit()

        print("Seeded guest session:")
        print(f"   hotel_slug : {HOTEL_SLUG}")
        print(f"   room_number: {ROOM_NUMBER}")
        print(f"   PIN        : {PIN}")
        print(f"   guest_name : {GUEST_NAME}")
        print(f"   session_id : {session.id}")
        print(f"   valid      : {session.checkin_date} → {session.checkout_date}")


if __name__ == "__main__":
    asyncio.run(main())
