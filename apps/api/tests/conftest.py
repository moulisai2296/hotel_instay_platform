"""Shared pytest fixtures for the InStayOS API.

Environment is configured *before* the app (and its lru_cache'd auth/limiter
singletons) is imported, so:
  - JWTs we mint here verify against the same AUTHKIT_SECRET_KEY the app uses;
  - AUTHKIT_DATABASE_URL is a dummy asyncpg URL — create_async_engine builds it
    lazily and never connects, since these tests are claims-only (no DB);
  - the global rate-limit default is small so the limiter is easy to exercise.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

os.environ.setdefault("AUTHKIT_SECRET_KEY", "test-secret-key-for-instayos-pytest-0123456789")
os.environ.setdefault(
    "AUTHKIT_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb"
)
os.environ.setdefault("RATE_LIMIT_DEFAULT", "3/minute")

import jwt  # noqa: E402  (PyJWT — pulled in by fast-authkit)
import pytest  # noqa: E402
import httpx  # noqa: E402
from fastapi import Depends  # noqa: E402

from main import create_app  # noqa: E402
from middleware import RequestContext, get_context, limiter, verify_path_hotel  # noqa: E402

SECRET = os.environ["AUTHKIT_SECRET_KEY"]
HOTEL_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
HOTEL_B = uuid.UUID("22222222-2222-2222-2222-222222222222")


def make_token(
    *,
    sub: str | None = None,
    app_role: str = "staff",
    hotel_id: uuid.UUID | None = HOTEL_A,
    department_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    token_type: str = "access",
    expired: bool = False,
) -> str:
    """Mint a JWT matching the InStayOS claims contract (HS256, same secret as authkit)."""
    now = datetime.now(timezone.utc)
    exp = now - timedelta(minutes=5) if expired else now + timedelta(minutes=15)
    payload = {
        "sub": sub or str(uuid.uuid4()),
        "type": token_type,
        "role": "authenticated",
        "app_role": app_role,
        "hotel_id": str(hotel_id) if hotel_id else None,
        "department_id": str(department_id) if department_id else None,
        "exp": exp,
    }
    if session_id:
        payload["session_id"] = str(session_id)
    return jwt.encode(payload, SECRET, algorithm="HS256")


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def app():
    """App with extra test-only routes that exercise the Step 3 primitives."""
    application = create_app()

    @application.get("/test/whoami")
    async def whoami(ctx: RequestContext = Depends(get_context)):
        return {"user_id": str(ctx.user_id), "app_role": ctx.app_role}

    @application.get("/test/hotels/{hotel_id}/resource")
    async def hotel_resource(hotel_id: uuid.UUID, ctx: RequestContext = Depends(verify_path_hotel)):
        return {"ok": True, "hotel_id": str(hotel_id)}

    @application.get("/test/limited")
    async def limited():
        return {"ok": True}

    return application


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture(autouse=True)
def reset_limiter():
    """Each test starts with empty rate-limit counters."""
    limiter.reset()
    yield
    limiter.reset()


# --- Guest PIN auth helpers (Step 4) -----------------------------------------

import bcrypt  # noqa: E402
from datetime import date, timedelta  # noqa: E402

from models import GuestSession  # noqa: E402
from services import ResolvedSession  # noqa: E402
from routers.guest import get_guest_auth_service  # noqa: E402

ROOM_A = uuid.UUID("33333333-3333-3333-3333-333333333333")
SESSION_A = uuid.UUID("44444444-4444-4444-4444-444444444444")
GUEST_PIN = "123456"


def make_guest_session(*, pin: str = GUEST_PIN, days_until_checkout: int = 2, **overrides):
    """A detached GuestSession (no DB) with a real bcrypt PIN hash."""
    today = date.today()
    fields = dict(
        id=SESSION_A,
        hotel_id=HOTEL_A,
        room_id=ROOM_A,
        guest_name="Test Guest",
        pin_hash=bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode(),
        checkin_date=today - timedelta(days=1),
        checkout_date=today + timedelta(days=days_until_checkout),
        is_checked_out=False,
    )
    fields.update(overrides)
    return GuestSession(**fields)


def make_resolved(session=None, room_number: str = "101", tz: str | None = "UTC"):
    """Wrap a session as the service's ResolvedSession (or None for 'no match')."""
    if session is None:
        return None
    return ResolvedSession(session=session, room_number=room_number, hotel_timezone=tz)


class _FakeGuestAuthService:
    """Stand-in for GuestAuthService that skips the DB."""

    def __init__(self, resolved):
        self.resolved = resolved
        self.recorded: list = []

    async def find_active_session(self, hotel_slug, room_number, today=None):
        return self.resolved

    async def record_token(self, session, token, expires_at):
        self.recorded.append((token, expires_at))


@pytest.fixture
def set_guest_service(app):
    """Install a fake guest-auth service returning the given ResolvedSession (or None)."""

    def _install(resolved) -> _FakeGuestAuthService:
        fake = _FakeGuestAuthService(resolved)
        app.dependency_overrides[get_guest_auth_service] = lambda: fake
        return fake

    yield _install
    app.dependency_overrides.pop(get_guest_auth_service, None)
