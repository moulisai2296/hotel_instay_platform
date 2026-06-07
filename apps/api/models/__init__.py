"""InStayOS SQLAlchemy models — typed mapping over the Supabase schema.

Importing this package registers every ORM class (including the fast-authkit
models) on the shared declarative ``Base``, so cross-table foreign keys and
relationships resolve regardless of import order. Import models from here:

    from models import Hotel, Request, User
"""

# fast-authkit models — keep them in the same registry as the business models
# so FKs like requests.assigned_to -> users.id resolve.
from auth.models import AuditLog, RefreshToken, User

from .base import (
    Base,
    DepartmentType,
    InputMode,
    OfferStatus,
    PmsProvider,
    RequestPriority,
    RequestStatus,
    StaffRole,
    TabletStatus,
)
from .tables import (
    Department,
    GuestInteraction,
    GuestSession,
    Hotel,
    Notification,
    Offer,
    PmsConnection,
    Request,
    RequestEvent,
    Room,
    Tablet,
)

__all__ = [
    # base / enums
    "Base",
    "StaffRole",
    "DepartmentType",
    "RequestStatus",
    "RequestPriority",
    "InputMode",
    "TabletStatus",
    "OfferStatus",
    "PmsProvider",
    # authkit
    "User",
    "RefreshToken",
    "AuditLog",
    # business tables
    "Hotel",
    "Department",
    "Room",
    "Tablet",
    "GuestSession",
    "Request",
    "RequestEvent",
    "Offer",
    "GuestInteraction",
    "PmsConnection",
    "Notification",
]
