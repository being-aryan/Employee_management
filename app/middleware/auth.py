import jwt
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.managers.auth_manager import AuthManager
from app.managers.jwt_service import JWTService

PUBLIC_PATHS = {
    "/api/v3/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}


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
                content={
                    "success": False,
                    "status_code": 401,
                    "message": "Bearer token is required",
                    "error_code": "NOT_AUTHENTICATED",
                    "details": [],
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = JWTService().verify_access_token(token.strip())
            admin_id = int(payload["sub"])
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "status_code": 401,
                    "message": "Invalid or expired authentication token",
                    "error_code": "INVALID_TOKEN",
                    "details": [],
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        admin = next(
            (user for user in AuthManager().users if user.id == admin_id),
            None,
        )

        if admin is None or not admin.is_active or admin.role != "admin":
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "status_code": 401,
                    "message": "Admin account is inactive or invalid",
                    "error_code": "INVALID_ADMIN",
                    "details": [],
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
