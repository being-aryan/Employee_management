from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.managers.auth_manager import AuthManager
from app.managers.jwt_service import JWTService
from app.schemas import Admin

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> Admin:
    """Validate the access token and return the authenticated admin."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    jwt_service = JWTService()

    try:
        payload = jwt_service.verify_access_token(token)
        admin_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise credentials_exception from None

    auth_manager = AuthManager()

    admin = next(
        (user for user in auth_manager.users if user.id == admin_id),
        None,
    )

    if admin is None or not admin.is_active or admin.role != "admin":
        raise credentials_exception

    return admin
