import os
from http import HTTPStatus

from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from auth import get_auth_kit
from auth.schemas import CustomUserRead
from middleware import limiter, rate_limit_handler
from routers import guest as guest_router


def _cors_origins() -> list[str]:
    """Allowed browser origins (comma-separated env), defaulting to local Next.js."""
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    app = FastAPI(title="InStayOS API", version="0.1.0")

    # Rate limiting: a global per-IP default applies to every route (covers
    # /auth/login). slowapi reads the limiter off app.state; SlowAPIMiddleware
    # performs the per-request check. Added before CORS so CORS stays the
    # OUTERMOST middleware — a 429 still carries CORS headers, otherwise the
    # browser would block the frontend from reading the rate-limit response.
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    # CORS — the Next.js frontend calls the API with cookies, so credentials must
    # be allowed (which requires explicit origins, never "*").
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Consistent error envelope: {"error": "...", "code": "..."} (CLAUDE.md).
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # A raiser can specify a precise body code via an "X-Error-Code" header
        # (e.g. HOTEL_MISMATCH, NOT_AUTHENTICATED); otherwise fall back to the
        # HTTP status name. The header is internal — strip it from the response.
        headers = dict(exc.headers or {})
        code = headers.pop("X-Error-Code", None)
        if code is None:
            try:
                code = HTTPStatus(exc.status_code).name
            except ValueError:
                code = "ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "code": code},
            headers=headers or None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation failed",
                "code": "VALIDATION_ERROR",
                "details": jsonable_encoder(exc.errors()),
            },
        )

    # Auth routes: /auth/login, /auth/refresh, /auth/logout, etc. The built-in
    # admin HTML router is intentionally NOT mounted — InStayOS has its own Next.js
    # admin panel (CLAUDE.md).
    auth_kit = get_auth_kit()
    auth_router = auth_kit.router
    # Replace authkit's built-in GET /me with our own so the response includes the
    # InStayOS profile fields (display_name, hotel_id, ...) via CustomUserRead.
    auth_router.routes = [r for r in auth_router.routes if getattr(r, "path", None) != "/me"]
    app.include_router(auth_router, prefix="/auth", tags=["auth"])

    @app.get("/auth/me", response_model=CustomUserRead, tags=["auth"])
    async def me(current_user=Depends(auth_kit.current_active_user)):
        """Current authenticated staff profile (InStayOS fields included)."""
        return current_user

    # Guest PIN auth (custom flow, not fast-authkit).
    app.include_router(guest_router.router)

    @app.get("/health", tags=["meta"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
