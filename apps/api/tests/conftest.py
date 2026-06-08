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
    room_id: uuid.UUID | None = None,
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
    if room_id:
        payload["room_id"] = str(room_id)
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


# --- Request creation + transcribe helpers (Step 6) --------------------------

from datetime import timezone  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from models.base import DepartmentType, RequestPriority, RequestStatus  # noqa: E402
from schemas.ai import ExtractedItem, IntentKind, IntentResult  # noqa: E402
from services.request_service import RequestService  # noqa: E402
import routers.requests as _requests_router  # noqa: E402
import routers.ai as _ai_router  # noqa: E402

DEPT_A = uuid.UUID("55555555-5555-5555-5555-555555555555")
DEPT_DEFAULT = uuid.UUID("66666666-6666-6666-6666-666666666666")


def guest_token() -> str:
    """A guest JWT carrying hotel/room/session, accepted by require_guest + get_context."""
    return make_token(
        app_role="guest", hotel_id=HOTEL_A, session_id=SESSION_A, room_id=ROOM_A
    )


def make_intent(**overrides) -> IntentResult:
    fields = dict(
        kind=IntentKind.service_request,
        department=DepartmentType.housekeeping,
        priority=RequestPriority.high,
        ai_title="Extra towels x2",
        items=[ExtractedItem(item="towel", qty=2)],
        sentiment=0.2,
        reason="guest asked for towels",
        guest_reply="Of course — towels are on the way!",
    )
    fields.update(overrides)
    return IntentResult(**fields)


class _FakeAIService:
    def __init__(self, intent: IntentResult):
        self._intent = intent

    async def classify_intent(self, text, hotel_context=None, history=None):
        return self._intent


class _FakeRequestRepo:
    """In-memory stand-in for RequestRepository; records what would be persisted."""

    def __init__(self, *, dept_id=DEPT_A, default_dept_id=DEPT_DEFAULT, hotel_context=None):
        self._dept_id = dept_id
        self._default = default_dept_id
        self._hotel_context = hotel_context or {
            "hotel_name": "Grand Hotel",
            "departments": ["housekeeping", "fb"],
        }
        self.persisted = None

    async def get_hotel_context(self, hotel_id):
        return self._hotel_context

    async def recent_interactions(self, session_id, limit=6):
        return []

    async def resolve_department_id(self, hotel_id, dept_type):
        return self._dept_id

    async def default_department_id(self, hotel_id):
        return self._default

    async def persist(self, request, event, interactions):
        if request is not None:
            # Mimic the DB assigning id/created_at and the server_default status.
            request.id = request.id or uuid.uuid4()
            request.created_at = datetime.now(timezone.utc)
            request.status = request.status or RequestStatus.pending
        self.persisted = SimpleNamespace(
            request=request, event=event, interactions=interactions
        )
        return request


@pytest.fixture
def set_request_service(app):
    """Install a RequestService built from a fake repo + fake AIService; returns the repo."""

    def _install(intent: IntentResult | None = None, **repo_kwargs) -> _FakeRequestRepo:
        repo = _FakeRequestRepo(**repo_kwargs)
        service = RequestService(repo, _FakeAIService(intent or make_intent()))
        app.dependency_overrides[_requests_router.get_request_service] = lambda: service
        return repo

    yield _install
    app.dependency_overrides.pop(_requests_router.get_request_service, None)


class _FakeVoiceService:
    def __init__(self, text="transcribed text"):
        self._text = text

    async def transcribe(self, audio: bytes, mimetype: str = "audio/wav") -> str:
        return self._text


@pytest.fixture
def set_voice_service(app):
    def _install(text="transcribed text") -> _FakeVoiceService:
        fake = _FakeVoiceService(text)
        app.dependency_overrides[_ai_router.get_voice] = lambda: fake
        return fake

    yield _install
    app.dependency_overrides.pop(_ai_router.get_voice, None)
