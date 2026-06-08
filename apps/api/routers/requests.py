"""Guest request creation (text). Voice notes go through /ai/transcribe first."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from middleware import RequestContext, require_guest
from schemas import CreateRequestRequest, CreateRequestResponse, RequestSummary
from schemas.ai import ExtractedItem
from services import RequestRepository, RequestService
from services.ai_service import get_ai_service

router = APIRouter(prefix="/requests", tags=["requests"])


def get_request_service(db: AsyncSession = Depends(get_db)) -> RequestService:
    """Provider for the request pipeline — overridden in tests with a fake."""
    return RequestService(RequestRepository(db), get_ai_service())


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
        summary = RequestSummary(
            id=request.id,
            status=request.status,
            priority=request.priority,
            department_id=request.department_id,
            ai_title=request.ai_title,
            items=[ExtractedItem(**item) for item in (request.ai_items or [])],
            sentiment=request.sentiment_score,
            created_at=request.created_at,
        )
        response.status_code = status.HTTP_201_CREATED  # a request was created
    return CreateRequestResponse(kind=kind, guest_reply=guest_reply, request=summary)
