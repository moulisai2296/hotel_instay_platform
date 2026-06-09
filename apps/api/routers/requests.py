"""Guest request creation (text) + staff status transitions.

Voice notes go through /ai/transcribe first. Reads (kanban / tracker) go straight
from Next.js via Supabase + RLS; only the writes live here.
"""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from middleware import RequestContext, require_guest, require_staff
from schemas import (
    CreateRequestRequest,
    CreateRequestResponse,
    RequestSummary,
    UpdateRequestStatusRequest,
)
from schemas.ai import ExtractedItem
from services import RequestRepository, RequestService, StaffRequestService
from services.ai_service import get_ai_service

router = APIRouter(prefix="/requests", tags=["requests"])


def get_request_service(db: AsyncSession = Depends(get_db)) -> RequestService:
    """Provider for the request pipeline — overridden in tests with a fake."""
    return RequestService(RequestRepository(db), get_ai_service())


def get_staff_request_service(
    db: AsyncSession = Depends(get_db),
) -> StaffRequestService:
    """Provider for staff request actions — overridden in tests with a fake."""
    return StaffRequestService(db)


def _to_summary(request) -> RequestSummary:
    return RequestSummary(
        id=request.id,
        status=request.status,
        priority=request.priority,
        department_id=request.department_id,
        ai_title=request.ai_title,
        items=[ExtractedItem(**item) for item in (request.ai_items or [])],
        sentiment=request.sentiment_score,
        created_at=request.created_at,
    )


@router.post("/create", response_model=CreateRequestResponse)
async def create_request(
    body: CreateRequestRequest,
    response: Response,
    ctx: RequestContext = Depends(require_guest),
    service: RequestService = Depends(get_request_service),
) -> CreateRequestResponse:
    """Handle a guest chat turn: classify, then route+persist a request, ask for a
    missing detail, or decline off-topic input — always returning a reply."""
    request, guest_reply, kind = await service.handle_message(
        ctx, body.raw_input, body.input_mode, body.voice_url
    )
    summary = None
    if request is not None:
        summary = _to_summary(request)
        response.status_code = status.HTTP_201_CREATED  # a request was created
    return CreateRequestResponse(kind=kind, guest_reply=guest_reply, request=summary)


@router.patch("/{request_id}/status", response_model=RequestSummary)
async def update_request_status(
    request_id: uuid.UUID,
    body: UpdateRequestStatusRequest,
    ctx: RequestContext = Depends(require_staff),
    service: StaffRequestService = Depends(get_staff_request_service),
) -> RequestSummary:
    """Staff action: move a request to a new status (kanban). Hotel + department
    isolation is enforced in the service from the staff JWT context."""
    request = await service.update_status(ctx, request_id, body.status, body.note)
    return _to_summary(request)
