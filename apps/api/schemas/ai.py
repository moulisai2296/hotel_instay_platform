"""Pydantic v2 schemas for the AI layer.

``IntentResult`` is the structured output of ``AIService.classify_intent`` and maps
directly onto the ``requests`` columns it feeds in Step 6 (``department_id`` via the
department type, ``priority``, ``ai_title``, ``ai_items``, ``sentiment_score``).
Typing the fields with the real Postgres-backed enums (``models.base``) means the
model is forced to choose a valid department/priority — invalid values fail
validation rather than reaching the DB.
"""

import enum
from typing import Optional

from pydantic import BaseModel, Field

from models.base import DepartmentType, RequestPriority


class IntentKind(str, enum.Enum):
    """What kind of message the guest sent — the primary guardrail.

    Only ``service_request`` creates a request. The other two keep the system from
    silently mishandling input: ``needs_info`` asks a clarifying question first, and
    ``unsupported`` (general/off-topic/jailbreak) gets a canned scope message.
    """

    service_request = "service_request"  # actionable hotel service → route + persist
    needs_info = "needs_info"            # a hotel request missing a required detail → ask
    unsupported = "unsupported"          # off-topic / not an in-stay service → decline


class ExtractedItem(BaseModel):
    """A concrete item the guest asked for, e.g. {item: "towel", qty: 2}."""

    item: str
    qty: int = Field(default=1, ge=1)


class IntentResult(BaseModel):
    """Structured classification of a guest message."""

    kind: IntentKind = IntentKind.service_request
    # Only meaningful for service_request; optional so the model isn't forced to
    # invent a department for off-topic / clarification messages.
    department: Optional[DepartmentType] = None
    priority: RequestPriority = RequestPriority.medium
    ai_title: str = ""
    items: list[ExtractedItem] = Field(default_factory=list)
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    reason: Optional[str] = None
    # A short, warm, guest-facing message produced in the same model call: a
    # confirmation (service_request) or a clarifying question (needs_info). For
    # unsupported it is overridden server-side with a deterministic scope message.
    guest_reply: str = ""
