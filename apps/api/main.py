import os
from http import HTTPStatus

from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from auth import get_auth_kit
from auth.schemas import CustomUserRead


def _cors_origins() -> list[str]:
    """Allowed browser origins (comma-separated env), defaulting to local Next.js."""
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    app = FastAPI(title="InStayOS API", version="0.1.0")

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
        try:
            code = HTTPStatus(exc.status_code).name
        except ValueError:
            code = "ERROR"
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "code": code})

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

    @app.get("/health", tags=["meta"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
