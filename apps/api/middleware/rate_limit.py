"""Application rate limiting (slowapi).

A single shared ``Limiter`` enforces a global default limit on every route via
``SlowAPIMiddleware``. The store is in-memory (``memory://``) — correct for a
single process; on multi-instance Railway the counters are per-process, so the
effective limit is N × the configured value until ``_storage_uri()`` is pointed
at a shared ``redis://...`` (the one-line seam for that move).

The global middleware keys by client IP, which is exactly right for *pre-auth*
brute-force defense (login, the upcoming guest PIN flow) — it runs before route
dependencies populate ``request.state.context``. For per-user / per-hotel limits
on routes we own, use ``@limiter.limit(LIMIT, key_func=get_user_or_ip_key)``,
where the context is already resolved.
"""

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Named limits for sensitive endpoints we'll own in later steps. Brute-forcing a
# 6-digit guest PIN (1M combos) is the motivating threat for PIN_VERIFY_LIMIT.
LOGIN_LIMIT = "10/minute"
PIN_VERIFY_LIMIT = "5/minute"


def _default_limit() -> str:
    """Global per-IP default; override with RATE_LIMIT_DEFAULT (e.g. for tests)."""
    return os.getenv("RATE_LIMIT_DEFAULT", "100/minute")


def _storage_uri() -> str:
    """In-memory by default. Set RATE_LIMIT_STORAGE_URI=redis://... for multi-instance."""
    return os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")


def get_user_or_ip_key(request: Request) -> str:
    """Key by authenticated principal when available, else client IP.

    Only meaningful on routes whose dependencies have already run (i.e. the
    ``@limiter.limit`` decorator), since ``request.state.context`` is populated
    by ``get_context``. The global middleware always falls through to IP.
    """
    ctx = getattr(request.state, "context", None)
    if ctx is not None:
        return f"user:{ctx.user_id}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_default_limit()],
    storage_uri=_storage_uri(),
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Render a 429 in the InStayOS ``{"error","code"}`` envelope with Retry-After.

    Must be a *synchronous* callable: ``SlowAPIMiddleware`` falls back to slowapi's
    default handler for any async handler, which would bypass this envelope.
    """
    try:
        retry_after = exc.limit.limit.get_expiry()
    except Exception:
        retry_after = 60
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests", "code": "RATE_LIMITED"},
        headers={"Retry-After": str(retry_after)},
    )
