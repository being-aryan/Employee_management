from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.managers.auth_manager import AuthManager
from app.managers.jwt_service import JWTService

bearer_scheme = HTTPBearer()


def get_current_admin(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
) -> object:
    token = credentials.credentials
    auth_manager = AuthManager()
    jwt_service = JWTService()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt_service.verify_access_token(token)
        admin_id = int(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise credentials_exception from None
    except Exception as exc:
        # Invalid, expired, or malformed JWT.
        import jwt

        if isinstance(exc, jwt.InvalidTokenError):
            raise credentials_exception from None
        raise

    admin = next(
        (user for user in auth_manager.users if user.id == admin_id),
        None,
    )

    if admin is None or not admin.is_active or admin.role != "admin":
        raise credentials_exception

    return admin
