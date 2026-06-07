import os
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from authkit_fastapi import AuthKit, AuthKitConfig

from .models import Base, User, RefreshToken, AuditLog

# =========================================================================
# Lazy initialization.
# The engine / sessionmaker / AuthKit are built on FIRST USE, not at import
# time, so importing this package (or the models) never opens a DB engine.
# Each factory is memoized with lru_cache => one shared instance per process.
# =========================================================================


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Create (once) the async SQLAlchemy engine from AUTHKIT_DATABASE_URL."""
    database_url = os.getenv("AUTHKIT_DATABASE_URL", "sqlite+aiosqlite:///./authkit.db")
    connect_args: dict = {}
    if "sqlite" in database_url:  # SQLite async needs this for cross-thread use
        connect_args["check_same_thread"] = False
    return create_async_engine(database_url, connect_args=connect_args, future=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Create (once) the async session factory bound to the engine."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)


def build_access_token_claims(user) -> dict:
    """Inject the InStayOS JWT Claims Contract into staff access tokens.

    See CLAUDE.md "JWT Claims Contract". Supabase RLS reads app_role/hotel_id from
    these claims and *requires* role == 'authenticated'. authkit's base payload
    already sets `sub` and `app_role` (= user.role); these custom claims are merged
    last (auth_service does payload.update(custom_claims)), so they add the rest.
    `session_id` is intentionally absent — it belongs to the guest PIN flow only.
    """
    return {
        "role": "authenticated",
        "app_role": getattr(user, "role", None),
        "hotel_id": str(user.hotel_id) if getattr(user, "hotel_id", None) else None,
        "department_id": str(user.department_id) if getattr(user, "department_id", None) else None,
    }


@lru_cache(maxsize=1)
def get_auth_kit() -> AuthKit:
    """Create (once) the fast-authkit engine wired to our models + session maker."""
    config = AuthKitConfig(
        access_token_claims=build_access_token_claims,
        # Staff/managers/admins are provisioned via the admin panel, not public
        # self-registration. (authkit's /register also hardcodes role='user' and
        # omits display_name, both of which violate our schema.)
        enable_register=False,
    )
    return AuthKit(
        config=config,
        db_session_maker=get_sessionmaker(),
        user_model=User,
        refresh_token_model=RefreshToken,
        audit_log_model=AuditLog,
    )


async def init_db() -> None:
    """Create tables from ORM metadata (dev/sandbox only).

    In prod the schema is owned by the Supabase SQL migrations — do NOT rely on
    this against the real database.
    """
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
