"""Pydantic v2 request/response schemas for the InStayOS API."""

from .guest import GuestProfile, VerifyPinRequest, VerifyPinResponse

__all__ = ["VerifyPinRequest", "VerifyPinResponse", "GuestProfile"]
