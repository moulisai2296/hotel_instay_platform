"""Guest chat turn: classify -> (route + persist a request | clarify | decline).

Every turn records the guest message + assistant reply in ``guest_interactions``;
only a ``service_request`` also writes a ``requests`` row + a "created" event. This
is the guardrail layer — off-topic input is declined with a deterministic scope
message and missing details trigger a clarifying question, so nothing is silently
turned into a bogus staff task.

Orchestration (``RequestService``) is kept separate from data access
(``RequestRepository``) so the logic is unit-testable with fake collaborators — no
DB, no model. Hotel isolation is structural: every read is filtered by, and every
write sets, ``ctx.hotel_id`` (from the guest JWT, never the request body).
"""

import uuid
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from middleware import RequestContext
from models import Department, GuestInteraction, Hotel, Request, RequestEvent
from models.base import DepartmentType, InputMode
from schemas.ai import IntentKind
from services.ai_service import AIService, build_scope_message

_HISTORY_LIMIT = 6  # recent turns passed to the model to resolve follow-ups

# Preferred catch-all departments when the AI's choice isn't active at this hotel.
_FALLBACK_ORDER = (DepartmentType.front_desk, DepartmentType.concierge)


class RequestRepository:
    """All DB access for request creation, scoped to one hotel."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_hotel_context(self, hotel_id: uuid.UUID) -> dict[str, Any]:
        """Hotel name + active department types — the context handed to classify_intent."""
        name = await self.db.scalar(select(Hotel.name).where(Hotel.id == hotel_id))
        types = (
            await self.db.execute(
                select(Department.type).where(
                    Department.hotel_id == hotel_id, Department.is_active.is_(True)
                )
            )
        ).scalars().all()
        return {"hotel_name": name, "departments": [t.value for t in types]}

    async def resolve_department_id(
        self, hotel_id: uuid.UUID, dept_type: DepartmentType
    ) -> Optional[uuid.UUID]:
        return await self.db.scalar(
            select(Department.id).where(
                Department.hotel_id == hotel_id,
                Department.type == dept_type,
                Department.is_active.is_(True),
            )
        )

    async def default_department_id(self, hotel_id: uuid.UUID) -> Optional[uuid.UUID]:
        """A safe landing department when the classified one isn't available here."""
        for dept_type in _FALLBACK_ORDER:
            found = await self.resolve_department_id(hotel_id, dept_type)
            if found:
                return found
        # else any active department for the hotel
        return await self.db.scalar(
            select(Department.id).where(
                Department.hotel_id == hotel_id, Department.is_active.is_(True)
            )
        )

    async def recent_interactions(
        self, session_id: uuid.UUID, limit: int = _HISTORY_LIMIT
    ) -> list[dict[str, str]]:
        """The last few chat turns for a session, oldest→newest, for follow-up context."""
        rows = (
            await self.db.execute(
                select(GuestInteraction.role, GuestInteraction.content)
                .where(GuestInteraction.guest_session_id == session_id)
                .order_by(GuestInteraction.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [{"role": role, "content": content} for role, content in reversed(rows)]

    async def persist(
        self,
        request: Optional[Request],
        event: Optional[RequestEvent],
        interactions: list[GuestInteraction],
    ) -> Optional[Request]:
        """Persist a chat turn. A request (+ its event) is optional; interactions always."""
        if request is not None:
            self.db.add(request)
            await self.db.flush()  # assign request.id before linking children
            if event is not None:
                event.request_id = request.id
                self.db.add(event)
            for interaction in interactions:
                interaction.request_id = request.id
            self.db.add_all(interactions)
            await self.db.commit()
            await self.db.refresh(request)
            return request
        self.db.add_all(interactions)
        await self.db.commit()
        return None


class RequestService:
    """Classify a guest message and persist the resulting request + audit trail."""

    def __init__(self, repo: RequestRepository, ai_service: AIService):
        self.repo = repo
        self.ai = ai_service

    async def handle_message(
        self,
        ctx: RequestContext,
        raw_input: str,
        input_mode: InputMode = InputMode.text,
        voice_url: str | None = None,
    ) -> tuple[Optional[Request], str, IntentKind]:
        """Process one guest chat turn.

        Returns ``(request_or_None, guest_reply, kind)``. A ``requests`` row is
        created only for ``service_request``; ``needs_info`` asks a clarifying
        question and ``unsupported`` returns a deterministic scope message — both
        without a request. Every turn is recorded in ``guest_interactions``.
        """
        hotel_context = await self.repo.get_hotel_context(ctx.hotel_id)
        history = await self.repo.recent_interactions(ctx.session_id)
        intent = await self.ai.classify_intent(raw_input, hotel_context, history)

        request: Optional[Request] = None
        event: Optional[RequestEvent] = None

        if intent.kind == IntentKind.unsupported:
            # Ignore any model free-text; reply with our own scoped message (injection-safe).
            guest_reply = build_scope_message(hotel_context.get("departments"))
        elif intent.kind == IntentKind.needs_info:
            guest_reply = intent.guest_reply or "Could you share a little more detail?"
        else:  # service_request
            department_id = (
                await self.repo.resolve_department_id(ctx.hotel_id, intent.department)
                if intent.department
                else None
            )
            if department_id is None:
                department_id = await self.repo.default_department_id(ctx.hotel_id)
            if department_id is None:
                raise HTTPException(
                    status_code=422,
                    detail="Hotel has no active department to route this request to",
                    headers={"X-Error-Code": "NO_DEPARTMENT"},
                )
            guest_reply = intent.guest_reply or "On its way!"
            request = Request(
                hotel_id=ctx.hotel_id,
                guest_session_id=ctx.session_id,
                room_id=ctx.room_id,
                department_id=department_id,
                raw_input=raw_input,
                input_mode=input_mode,
                voice_url=voice_url,
                ai_title=intent.ai_title or raw_input[:80],
                ai_items=[item.model_dump() for item in intent.items],
                ai_priority_reason=intent.reason,
                priority=intent.priority,
                sentiment_score=intent.sentiment,
            )
            event = RequestEvent(
                hotel_id=ctx.hotel_id,
                actor_type="guest",
                actor_id=ctx.session_id,
                event_type="created",
                to_status="pending",
            )

        interactions = [
            GuestInteraction(
                hotel_id=ctx.hotel_id,
                guest_session_id=ctx.session_id,
                role="guest",
                content=raw_input,
                input_mode=input_mode,
                sentiment_score=intent.sentiment,
            ),
            GuestInteraction(
                hotel_id=ctx.hotel_id,
                guest_session_id=ctx.session_id,
                role="assistant",
                content=guest_reply,
            ),
        ]
        saved = await self.repo.persist(request, event, interactions)
        return saved, guest_reply, intent.kind
