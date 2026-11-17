import jwt
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.managers.auth_manager import AuthManager
from app.managers.jwt_service import JWTService

PUBLIC_PATHS = {
    "/api/v3/auth/login",
    "/api/v3/auth/verify-otp",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/openapi.json",
}


async def is_authorized_admin(admin_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        admin = await AuthManager(session).get_admin_by_id(admin_id)
        return admin is not None and admin.is_active and admin.role == "admin"


def add_auth_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def authenticate_request(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")

        if scheme.lower() != "bearer" or not token.strip():
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = JWTService().verify_access_token(token.strip())
            admin_id = int(payload["sub"])

        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            is_admin = await is_authorized_admin(admin_id)
        except SQLAlchemyError:
            return JSONResponse(
                status_code=503,
                content={"detail": "Authentication service temporarily unavailable"},
            )

        if not is_admin:
            return JSONResponse(
                status_code=401,
                content={"detail": "Admin not found or inactive"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
