"""Guest PIN authentication routes (custom flow — not fast-authkit).

Mobile-first: the hotel is identified by the URL slug the guest's phone opens, the
guest types room number + 6-digit PIN, and on success receives a short-lived guest
JWT. ``GUEST_ACCESS_MODE`` reserves the seam for a future tablet resolver.
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from middleware import RequestContext, limiter, require_guest
from middleware.rate_limit import PIN_VERIFY_LIMIT
from schemas import GuestProfile, VerifyPinRequest, VerifyPinResponse
from services import GuestAuthService
from services.guest_auth_service import (
    build_guest_claims,
    burn_dummy_check,
    compute_token_expiry,
    mint_guest_token,
    verify_pin,
)

router = APIRouter(prefix="/guest", tags=["guest"])

# Uniform failure for every PIN/room/hotel mismatch — never reveal which part was
# wrong (anti-enumeration). Pairs with the timing equalizer in the service.
_INVALID = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid room or PIN",
    headers={"X-Error-Code": "INVALID_CREDENTIALS"},
)


def _mobile_enabled() -> bool:
    """GUEST_ACCESS_MODE: 'mobile' (default), 'tablet', or 'both'. Tablet = later step."""
    return os.getenv("GUEST_ACCESS_MODE", "mobile") in ("mobile", "both")


def get_guest_auth_service(db: AsyncSession = Depends(get_db)) -> GuestAuthService:
    """Provider for the data-access seam — overridden in tests with a fake."""
    return GuestAuthService(db)


@router.post("/verify-pin", response_model=VerifyPinResponse)
@limiter.limit(PIN_VERIFY_LIMIT)
async def verify_pin_endpoint(
    request: Request,  # required by slowapi's limiter
    body: VerifyPinRequest,
    service: GuestAuthService = Depends(get_guest_auth_service),
) -> VerifyPinResponse:
    """Verify a guest's room + PIN and issue a guest JWT (expires at checkout)."""
    if not _mobile_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mobile guest access is disabled for this deployment",
            headers={"X-Error-Code": "MODE_DISABLED"},
        )

    today = datetime.now(timezone.utc).date()
    resolved = await service.find_active_session(body.hotel_slug, body.room_number, today)
    if resolved is None:
        burn_dummy_check(body.pin)  # equalize timing vs. a real verify
        raise _INVALID

    session = resolved.session
    if not verify_pin(body.pin, session.pin_hash):
        raise _INVALID

    expires_at = compute_token_expiry(session.checkout_date, resolved.hotel_timezone)
    token = mint_guest_token(build_guest_claims(session, resolved.room_number, expires_at))
    await service.record_token(session, token, expires_at)

    return VerifyPinResponse(
        access_token=token,
        expires_at=expires_at,
        guest=GuestProfile(
            session_id=session.id,
            guest_name=session.guest_name,
            room_number=resolved.room_number,
            hotel_id=session.hotel_id,
            checkout_date=session.checkout_date,
        ),
    )


@router.get("/me")
async def guest_me(ctx: RequestContext = Depends(require_guest)) -> dict:
    """The current guest's own session context (from their JWT)."""
    return {
        "session_id": str(ctx.session_id) if ctx.session_id else None,
        "hotel_id": str(ctx.hotel_id) if ctx.hotel_id else None,
        "room_id": str(ctx.room_id) if ctx.room_id else None,
        "app_role": ctx.app_role,
    }
