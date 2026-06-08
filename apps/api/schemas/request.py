"""Pydantic v2 schemas for guest request creation + voice transcription.

The request body intentionally carries NO hotel_id / room_id / session_id — those
are read only from the guest JWT (hotel isolation; CLAUDE.md). The client supplies
just the message and how it was entered.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from models.base import InputMode, RequestPriority, RequestStatus
from schemas.ai import ExtractedItem, IntentKind


class CreateRequestRequest(BaseModel):
    raw_input: str = Field(min_length=1)
    input_mode: InputMode = InputMode.text
    voice_url: str | None = None  # set by the client after /ai/transcribe (storage later)


class RequestSummary(BaseModel):
    id: uuid.UUID
    status: RequestStatus
    priority: RequestPriority
    department_id: uuid.UUID  # the routed department (may differ from the AI's pick after fallback)
    ai_title: str | None = None
    items: list[ExtractedItem] = Field(default_factory=list)
    sentiment: float | None = None
    created_at: datetime


class CreateRequestResponse(BaseModel):
    """A chat-turn result. `request` is present only when kind == service_request."""

    kind: IntentKind
    guest_reply: str
    request: RequestSummary | None = None


class TranscribeResponse(BaseModel):
    text: str
