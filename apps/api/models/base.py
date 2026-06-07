"""Shared declarative base + Postgres enum types for the InStayOS mapping layer.

DB-first design: the schema is owned by the SQL migrations in
``supabase/migrations/``. These SQLAlchemy models are a *typed mapping* over the
already-existing tables — they are never used to create or alter the schema
(no ``create_all``, no Alembic autogenerate against business tables).

We reuse fast-authkit's ``Base`` so the authkit models (User/RefreshToken/
AuditLog) and the InStayOS models share one registry, which lets relationships
and foreign keys resolve across both packages.
"""

import enum

from sqlalchemy import Enum as SAEnum

# Single shared DeclarativeBase / registry (same one auth/models.py uses).
from authkit_fastapi.models import Base  # re-exported below

__all__ = [
    "Base",
    "pg_enum",
    "StaffRole",
    "DepartmentType",
    "RequestStatus",
    "RequestPriority",
    "InputMode",
    "TabletStatus",
    "OfferStatus",
    "PmsProvider",
]


# --- Python enums mirroring the Postgres enum types (migration 0001) ---------
class StaffRole(str, enum.Enum):
    staff = "staff"
    dept_manager = "dept_manager"
    hotel_manager = "hotel_manager"
    admin = "admin"


class DepartmentType(str, enum.Enum):
    housekeeping = "housekeeping"
    fb = "fb"
    maintenance = "maintenance"
    concierge = "concierge"
    spa = "spa"
    front_desk = "front_desk"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    escalated = "escalated"
    cancelled = "cancelled"


class RequestPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class InputMode(str, enum.Enum):
    text = "text"
    voice = "voice"
    chip = "chip"


class TabletStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    maintenance = "maintenance"


class OfferStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    claimed = "claimed"


class PmsProvider(str, enum.Enum):
    cloudbeds = "cloudbeds"
    mews = "mews"
    opera = "opera"
    apaleo = "apaleo"
    manual = "manual"


def pg_enum(python_enum: type[enum.Enum], name: str) -> SAEnum:
    """Map a Python enum onto an existing Postgres enum type.

    ``create_type=False`` is critical: the enum types are owned by SQL migration
    0001, so SQLAlchemy must never try to emit ``CREATE TYPE``. ``values_callable``
    sends the enum *values* (the labels Postgres knows), not the member names.
    """
    return SAEnum(
        python_enum,
        name=name,
        create_type=False,
        native_enum=True,
        values_callable=lambda e: [member.value for member in e],
    )
