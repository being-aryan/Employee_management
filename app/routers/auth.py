from fastapi import APIRouter, Depends, HTTPException, status

from app.managers.auth_manager import AuthManager
from app.managers.jwt_service import JWTService
from app.schemas import AdminLogin, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_manager() -> AuthManager:
    return AuthManager()


def get_jwt_service() -> JWTService:
    return JWTService()


@router.post("/login", response_model=TokenResponse)
def admin_login(
    credentials: AdminLogin,
    auth_manager: AuthManager = Depends(get_auth_manager),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    admin = auth_manager.authenticate_admin(
        str(credentials.email),
        credentials.password,
    )

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = jwt_service.create_access_token(str(admin.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
