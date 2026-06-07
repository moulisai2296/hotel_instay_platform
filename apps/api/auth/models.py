import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Uuid, ForeignKey, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from authkit_fastapi.models import Base, BaseUserMixin, BaseRefreshTokenMixin, BaseAuditLogMixin

# =========================================================================
# Customize Your Database Schema Here
# You can add custom columns, constraints, or relationships.
# After changes, generate migration script with Alembic.
# =========================================================================

class User(Base, BaseUserMixin):
    __tablename__ = "users"

   
    # --- InStayOS staff fields (columns already exist in migration 0002) -----
    # Override BaseUserMixin's plain-string `role` with the native `staff_role`
    # Postgres enum, otherwise asyncpg binds a VARCHAR that won't implicitly cast
    # to the enum on INSERT. Values stay plain strings in Python (authkit-friendly).
    # Valid labels: staff|dept_manager|hotel_manager|admin — the mixin default
    # "user" is NOT valid, so always set one of these.
    role: Mapped[Optional[str]] = mapped_column(
        SAEnum(
            "staff", "dept_manager", "hotel_manager", "admin",
            name="staff_role", native_enum=True, create_type=False,
        ),
        nullable=True,
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    hotel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("hotels.id", ondelete="CASCADE"), index=True, nullable=True
    )  # NULL for super-admin
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="SET NULL"), index=True, nullable=True
    )  # NULL for managers/admin
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )

class RefreshToken(Base, BaseRefreshTokenMixin):
    __tablename__ = "refresh_tokens"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

class AuditLog(Base, BaseAuditLogMixin):
    __tablename__ = "audit_logs"
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, 
        ForeignKey("users.id", ondelete="SET NULL"), 
        index=True, 
        nullable=True
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
