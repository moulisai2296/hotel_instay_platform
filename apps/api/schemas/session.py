"""Schemas for the staff-side manual guest check-in (room + PIN allocation).

Distinct from ``guest.py`` (the guest's own PIN-verify flow): here a manager
creates the stay and the response returns the generated PIN **once** so it can be
handed to the guest (it is only ever stored hashed).
"""

import uuid
from datetime import date

from pydantic import BaseModel, Field, model_validator


class CreateGuestSessionRequest(BaseModel):
    room_number: str = Field(min_length=1, max_length=20)
    guest_name: str = Field(min_length=1, max_length=120)
    checkout_date: date
    checkin_date: date | None = None  # defaults to today in the service
    num_guests: int = Field(default=1, ge=1, le=20)
    guest_email: str | None = Field(default=None, max_length=200)
    # Optional: let staff set a PIN; otherwise one is generated.
    pin: str | None = Field(default=None, pattern=r"^\d{6}$")

    @model_validator(mode="after")
    def _check_dates(self) -> "CreateGuestSessionRequest":
        start = self.checkin_date or date.today()
        if self.checkout_date < start:
            raise ValueError("checkout_date must be on or after check-in")
        return self


class CreateGuestSessionResponse(BaseModel):
    session_id: uuid.UUID
    room_number: str
    guest_name: str
    pin: str  # plaintext — shown ONCE; stored only as a bcrypt hash
    checkin_date: date
    checkout_date: date
