"""Staff-side guest session management (manual check-in).

Reads (active-guests lists) go from Next.js via Supabase + RLS; this is the
write path. Manager/admin only — see onboarding-roles-pms decision.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from middleware import RequestContext, require_manager
from schemas import CreateGuestSessionRequest, CreateGuestSessionResponse
from services import GuestSessionService

router = APIRouter(prefix="/guest-sessions", tags=["guest-sessions"])


def get_guest_session_service(
    db: AsyncSession = Depends(get_db),
) -> GuestSessionService:
    """Provider for the check-in service — overridden in tests with a fake."""
    return GuestSessionService(db)


@router.post(
    "", response_model=CreateGuestSessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_guest_session(
    body: CreateGuestSessionRequest,
    ctx: RequestContext = Depends(require_manager),
    service: GuestSessionService = Depends(get_guest_session_service),
) -> CreateGuestSessionResponse:
    """Check a guest in: allocate the room + mint a 6-digit PIN, returned once."""
    session, pin = await service.create_session(
        ctx,
        room_number=body.room_number,
        guest_name=body.guest_name,
        checkout_date=body.checkout_date,
        checkin_date=body.checkin_date,
        num_guests=body.num_guests,
        guest_email=body.guest_email,
        pin=body.pin,
    )
    return CreateGuestSessionResponse(
        session_id=session.id,
        room_number=body.room_number,
        guest_name=session.guest_name,
        pin=pin,
        checkin_date=session.checkin_date,
        checkout_date=session.checkout_date,
    )
