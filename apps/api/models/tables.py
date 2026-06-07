"""SQLAlchemy ORM models mapping the InStayOS business tables.

These mirror ``supabase/migrations/20260606090002_tables.sql`` (the schema
authority). Column defaults use ``server_default`` so inserts can omit
DB-provided values; relationships are one-directional (no ``back_populates``) to
keep the mapping simple — load them explicitly with ``selectinload`` in async
queries.

The ``users`` table is mapped by ``auth.models.User`` (fast-authkit). Foreign
keys here reference ``users.id`` and relationships resolve via the shared
registry — see ``models/__init__.py``.
"""

import uuid
from datetime import date, datetime, time
from typing import Any, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import (
    Base,
    DepartmentType,
    InputMode,
    OfferStatus,
    PmsProvider,
    RequestPriority,
    RequestStatus,
    TabletStatus,
    pg_enum,
)


# 1. hotels — root tenant entity ----------------------------------------------
class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(Text)
    country: Mapped[Optional[str]] = mapped_column(Text)
    total_rooms: Mapped[Optional[int]] = mapped_column(Integer)
    property_type: Mapped[Optional[str]] = mapped_column(Text)
    timezone: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    subscription_tier: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# 2. departments --------------------------------------------------------------
class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[DepartmentType] = mapped_column(
        pg_enum(DepartmentType, "department_type"), nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    working_hours_start: Mapped[Optional[time]] = mapped_column(Time)
    working_hours_end: Mapped[Optional[time]] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    hotel: Mapped["Hotel"] = relationship()


# 3. rooms --------------------------------------------------------------------
class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_number: Mapped[str] = mapped_column(Text, nullable=False)
    room_type: Mapped[Optional[str]] = mapped_column(Text)
    floor: Mapped[Optional[int]] = mapped_column(Integer)
    max_occupancy: Mapped[Optional[int]] = mapped_column(Integer)
    pms_room_id: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    hotel: Mapped["Hotel"] = relationship()


# 4. tablets ------------------------------------------------------------------
class Tablet(Base):
    __tablename__ = "tablets"
    __table_args__ = (UniqueConstraint("hotel_id", "tablet_code", name="tablets_hotel_id_tablet_code_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tablet_code: Mapped[str] = mapped_column(Text, nullable=False)
    location_name: Mapped[str] = mapped_column(Text, nullable=False)
    location_type: Mapped[Optional[str]] = mapped_column(Text)
    room_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("rooms.id", ondelete="SET NULL")
    )
    status: Mapped[TabletStatus] = mapped_column(
        pg_enum(TabletStatus, "tablet_status"), nullable=False, server_default=text("'offline'")
    )
    last_ping_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    device_info: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    hotel: Mapped["Hotel"] = relationship()
    room: Mapped[Optional["Room"]] = relationship()


# 6. guest_sessions — one per guest stay; custom PIN auth lives here -----------
class GuestSession(Base):
    __tablename__ = "guest_sessions"
    __table_args__ = (
        CheckConstraint("satisfaction_score between 1 and 5", name="guest_sessions_satisfaction_score_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    guest_name: Mapped[str] = mapped_column(Text, nullable=False)
    guest_email: Mapped[Optional[str]] = mapped_column(Text)
    guest_phone: Mapped[Optional[str]] = mapped_column(Text)
    nationality: Mapped[Optional[str]] = mapped_column(Text)
    pin_hash: Mapped[str] = mapped_column(Text, nullable=False)  # bcrypt(6-digit PIN)
    checkin_date: Mapped[date] = mapped_column(Date, nullable=False)
    checkout_date: Mapped[date] = mapped_column(Date, nullable=False)
    num_guests: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    pms_booking_id: Mapped[Optional[str]] = mapped_column(Text)
    is_checked_out: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    satisfaction_score: Mapped[Optional[int]] = mapped_column(SmallInteger)
    session_token: Mapped[Optional[str]] = mapped_column(Text)  # JWT after PIN verified
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    hotel: Mapped["Hotel"] = relationship()
    room: Mapped["Room"] = relationship()


# 7. requests (CORE) ----------------------------------------------------------
class Request(Base):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    guest_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    tablet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("tablets.id", ondelete="SET NULL")
    )
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    input_mode: Mapped[Optional[InputMode]] = mapped_column(pg_enum(InputMode, "input_mode"))
    voice_url: Mapped[Optional[str]] = mapped_column(Text)
    ai_title: Mapped[Optional[str]] = mapped_column(Text)
    ai_items: Mapped[Optional[Any]] = mapped_column(JSONB)
    ai_priority_reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[RequestStatus] = mapped_column(
        pg_enum(RequestStatus, "request_status"), nullable=False, server_default=text("'pending'")
    )
    priority: Mapped[RequestPriority] = mapped_column(
        pg_enum(RequestPriority, "request_priority"), nullable=False, server_default=text("'medium'")
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1.0 to 1.0
    location_context: Mapped[Optional[str]] = mapped_column(Text)
    staff_notes: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolution_time_mins: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    hotel: Mapped["Hotel"] = relationship()
    guest_session: Mapped["GuestSession"] = relationship()
    room: Mapped["Room"] = relationship()
    department: Mapped["Department"] = relationship()
    tablet: Mapped[Optional["Tablet"]] = relationship()
    events: Mapped[list["RequestEvent"]] = relationship()


# 8. request_events — IMMUTABLE append-only audit trail -----------------------
class RequestEvent(Base):
    __tablename__ = "request_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_type: Mapped[str] = mapped_column(Text, nullable=False)  # guest/staff/system/ai
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)  # user.id or guest_session.id
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    from_status: Mapped[Optional[RequestStatus]] = mapped_column(pg_enum(RequestStatus, "request_status"))
    to_status: Mapped[Optional[RequestStatus]] = mapped_column(pg_enum(RequestStatus, "request_status"))
    note: Mapped[Optional[str]] = mapped_column(Text)
    # 'metadata' is reserved on the declarative Base — map the column under a safe attr name.
    event_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# 9. offers -------------------------------------------------------------------
class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint("discount_pct between 0 and 100", name="offers_discount_pct_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    discount_pct: Mapped[Optional[int]] = mapped_column(SmallInteger)
    original_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[OfferStatus] = mapped_column(
        pg_enum(OfferStatus, "offer_status"), nullable=False, server_default=text("'active'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    hotel: Mapped["Hotel"] = relationship()


# 10. guest_interactions — full AI chat history -------------------------------
class GuestInteraction(Base):
    __tablename__ = "guest_interactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    guest_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)  # guest/assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    input_mode: Mapped[Optional[InputMode]] = mapped_column(pg_enum(InputMode, "input_mode"))
    request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("requests.id", ondelete="SET NULL")
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    guest_session: Mapped["GuestSession"] = relationship()


# 11. pms_connections — one per hotel -----------------------------------------
class PmsConnection(Base):
    __tablename__ = "pms_connections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    provider: Mapped[PmsProvider] = mapped_column(pg_enum(PmsProvider, "pms_provider"), nullable=False)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text)  # AES-256 at rest
    api_endpoint: Mapped[Optional[str]] = mapped_column(Text)
    is_connected: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_sync_status: Mapped[Optional[str]] = mapped_column(Text)
    sync_config: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    hotel: Mapped["Hotel"] = relationship()


# 12. notifications -----------------------------------------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text)
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)  # request_id or guest_session_id
    is_read: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
