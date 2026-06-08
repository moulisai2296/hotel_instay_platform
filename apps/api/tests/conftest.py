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
