"""Pydantic v2 request/response schemas for the InStayOS API."""

from .ai import ExtractedItem, IntentKind, IntentResult
from .guest import GuestProfile, VerifyPinRequest, VerifyPinResponse
from .request import (
    CreateRequestRequest,
    CreateRequestResponse,
    RequestSummary,
    TranscribeResponse,
)

__all__ = [
    "VerifyPinRequest",
    "VerifyPinResponse",
    "GuestProfile",
    "IntentResult",
    "IntentKind",
    "ExtractedItem",
    "CreateRequestRequest",
    "CreateRequestResponse",
    "RequestSummary",
    "TranscribeResponse",
]
