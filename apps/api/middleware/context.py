"""Per-request tenant context + hotel-isolation guard.

The FastAPI backend talks to Supabase with the **service role key**, which
bypasses Row Level Security. RLS therefore protects the Next.js read path but
NOT this API. Hotel isolation is consequently an *application-layer*
responsibility (CLAUDE.md: "hotel isolation done in middleware").

This module turns the signed JWT claims contract into a typed
``RequestContext`` and offers a boundary guard that rejects cross-hotel access.
It is implemented as FastAPI **dependencies** rather than Starlette
``BaseHTTPMiddleware`` because isolation must distinguish public from protected
routes, emit the ``{"error","code"}`` envelope on 401/403, and compose with
``auth_kit.requires_roles(...)`` — none of which a blanket middleware does well.

Protected routers should be created so every route carries the context::

    router = APIRouter(dependencies=[Depends(get_context)])

JWT decoding is delegated to authkit's ``auth_service`` so the secret
(``AUTHKIT_SECRET_KEY`` == ``SUPABASE_JWT_SECRET``) and algorithm stay in one
place — never hand-roll ``jwt.decode`` here.
"""

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from auth import get_auth_kit


class RequestContext(BaseModel):
    """The authenticated tenant scope for a single request.

    Built from JWT claims only (no DB round-trip), so it is cheap but reflects
    the token at sign time: a token revoked mid-life still resolves here until
    it expires (~15 min for access tokens). Routes that must honour revocation
    should additionally depend on ``auth_kit.current_active_user``, which hits
    the DB.
    """

    model_config = ConfigDict(frozen=True)

    user_id: uuid.UUID  # JWT `sub` — users.id (staff) or guest_sessions.id (guest)
    app_role: str  # staff | dept_manager | hotel_manager | admin | guest
    hotel_id: Optional[uuid.UUID] = None  # NULL only for the platform super-admin
    department_id: Optional[uuid.UUID] = None  # staff / dept_manager only
    session_id: Optional[uuid.UUID] = None  # guests only (PIN flow)
    room_id: Optional[uuid.UUID] = None  # guests only — the room their stay is in

    @property
    def is_super_admin(self) -> bool:
        """Platform operator: not bound to any single hotel, so isolation is bypassed."""
        return self.app_role == "admin" and self.hotel_id is None


def _unauthorized(detail: str, code: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer", "X-Error-Code": code},
    )


async def get_context(request: Request) -> RequestContext:
    """Resolve and cache the ``RequestContext`` for a protected route.

    Reuses authkit's token extraction (cookie `authkit_access` then bearer) and
    `decode_token`. Raises 401 when the token is missing, malformed, or not an
    access token.
    """
    cached = getattr(request.state, "context", None)
    if isinstance(cached, RequestContext):
        return cached

    auth_kit = get_auth_kit()
    token = await auth_kit.dependencies.get_token_from_request(request)
    if not token:
        raise _unauthorized("Not authenticated", "NOT_AUTHENTICATED")

    payload = auth_kit.auth_service.decode_token(token)
    if not payload or payload.get("type") != "access":
        raise _unauthorized("Invalid or expired access token", "INVALID_TOKEN")

    try:
        ctx = RequestContext(
            user_id=payload["sub"],
            app_role=payload.get("app_role"),
            hotel_id=payload.get("hotel_id"),
            department_id=payload.get("department_id"),
            session_id=payload.get("session_id"),
            room_id=payload.get("room_id"),
        )
    except (KeyError, ValueError):
        # `sub`/`app_role` missing or a claim is not a valid UUID.
        raise _unauthorized("Malformed token claims", "INVALID_TOKEN")

    request.state.context = ctx
    return ctx


def assert_hotel_access(ctx: RequestContext, target_hotel_id: uuid.UUID) -> None:
    """Guard a hotel-scoped resource against cross-tenant access.

    The platform super-admin (``hotel_id is None``) may act on any hotel; every
    other principal may only touch its own ``hotel_id``. Raises 403 otherwise.
    """
    if ctx.is_super_admin:
        return
    if ctx.hotel_id != target_hotel_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resource belongs to a different hotel",
            headers={"X-Error-Code": "HOTEL_MISMATCH"},
        )


async def verify_path_hotel(
    hotel_id: uuid.UUID, ctx: RequestContext = Depends(get_context)
) -> RequestContext:
    """Dependency for ``/.../{hotel_id}/...`` routes: enforce the path matches the token."""
    assert_hotel_access(ctx, hotel_id)
    return ctx


async def require_guest(ctx: RequestContext = Depends(get_context)) -> RequestContext:
    """Restrict a route to guest-PIN principals (``app_role == "guest"``)."""
    if ctx.app_role != "guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guests only",
            headers={"X-Error-Code": "GUEST_ONLY"},
        )
    return ctx


_STAFF_ROLES = frozenset({"staff", "dept_manager", "hotel_manager", "admin"})


async def require_staff(ctx: RequestContext = Depends(get_context)) -> RequestContext:
    """Restrict a route to hotel staff principals (any non-guest role)."""
    if ctx.app_role not in _STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff only",
            headers={"X-Error-Code": "STAFF_ONLY"},
        )
    return ctx


_MANAGER_ROLES = frozenset({"hotel_manager", "admin"})


async def require_manager(ctx: RequestContext = Depends(get_context)) -> RequestContext:
    """Restrict a route to hotel managers / admins (e.g. guest check-in)."""
    if ctx.app_role not in _MANAGER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin only",
            headers={"X-Error-Code": "MANAGER_ONLY"},
        )
    return ctx
