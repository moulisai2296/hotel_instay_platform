"""Pydantic v2 schemas for the guest PIN auth flow (mobile-first)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class VerifyPinRequest(BaseModel):
    """Mobile locator: hotel comes from the URL slug, room + PIN typed by the guest."""

    hotel_slug: str = Field(min_length=1)
    room_number: str = Field(min_length=1)
    pin: str = Field(pattern=r"^\d{6}$", description="6-digit numeric PIN")


class GuestProfile(BaseModel):
    """The guest's own stay details, returned alongside the token."""

    session_id: uuid.UUID
    guest_name: str
    room_number: str
    hotel_id: uuid.UUID
    checkout_date: date


class VerifyPinResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    guest: GuestProfile
