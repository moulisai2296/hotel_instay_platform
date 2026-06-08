"""Pydantic v2 schemas for the AI layer.

``IntentResult`` is the structured output of ``AIService.classify_intent`` and maps
directly onto the ``requests`` columns it feeds in Step 6 (``department_id`` via the
department type, ``priority``, ``ai_title``, ``ai_items``, ``sentiment_score``).
Typing the fields with the real Postgres-backed enums (``models.base``) means the
model is forced to choose a valid department/priority — invalid values fail
validation rather than reaching the DB.
"""

from typing import Optional

from pydantic import BaseModel, Field

from models.base import DepartmentType, RequestPriority


class ExtractedItem(BaseModel):
    """A concrete item the guest asked for, e.g. {item: "towel", qty: 2}."""

    item: str
    qty: int = Field(default=1, ge=1)


class IntentResult(BaseModel):
    """Structured classification of a guest request."""

    department: DepartmentType
    priority: RequestPriority = RequestPriority.medium
    ai_title: str
    items: list[ExtractedItem] = Field(default_factory=list)
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    reason: Optional[str] = None
