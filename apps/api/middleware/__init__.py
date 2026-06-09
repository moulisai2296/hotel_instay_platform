"""Hotel-isolation context + rate-limiting primitives (CLAUDE.md `middleware/`)."""

from .context import (
    RequestContext,
    assert_hotel_access,
    get_context,
    require_guest,
    require_staff,
    verify_path_hotel,
)
from .rate_limit import (
    LOGIN_LIMIT,
    PIN_VERIFY_LIMIT,
    get_user_or_ip_key,
    limiter,
    rate_limit_handler,
)

__all__ = [
    "RequestContext",
    "get_context",
    "assert_hotel_access",
    "verify_path_hotel",
    "require_guest",
    "require_staff",
    "limiter",
    "rate_limit_handler",
    "get_user_or_ip_key",
    "LOGIN_LIMIT",
    "PIN_VERIFY_LIMIT",
]
