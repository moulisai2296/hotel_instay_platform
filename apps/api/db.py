"""Async DB session dependency for the InStayOS business tables.

fast-authkit manages its own session for the auth models; this is the dependency
for *our* tables (`models/tables.py`). Both share one engine/sessionmaker
(`auth/setup.py`), so there is a single connection pool per process.
"""

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from auth.setup import get_sessionmaker


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async session, closed on completion."""
    async with get_sessionmaker()() as session:
        yield session
