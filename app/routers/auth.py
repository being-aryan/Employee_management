
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database_dependencies import get_db
from app.managers.auth_manager import AuthManager
from app.managers.jwt_service import JWTService
from app.managers.otp_manager import OTPManager
from app.redis_client import redis_client
from app.schemas import (
    AdminLogin,
    OTPChallengeResponse,
    OTPVerificationRequest,
    TokenResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/login",
    response_model=OTPChallengeResponse,
)
async def admin_login(
    credentials: AdminLogin,
    session: DatabaseSession,
) -> OTPChallengeResponse:
    auth_manager = AuthManager(session)

    admin = await auth_manager.authenticate_admin(
        str(credentials.email),
        credentials.password,
    )

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    otp_manager = OTPManager(
        redis_client=redis_client,
        secret_key=bytes.fromhex(settings.otp_hmac_secret_key),
    )

    challenge_id, otp = await otp_manager.create_challenge(
        admin_id=admin.id,
    )

    if settings.environment == "development":
        print(f"Development OTP for admin {admin.id}: {otp}")

    return OTPChallengeResponse(
        message="OTP generated successfully",
        challenge_id=challenge_id,
        expires_in=OTPManager.OTP_EXPIRY_SECONDS,
    )


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
)
async def verify_admin_otp(
    payload: OTPVerificationRequest,
    session: DatabaseSession,
) -> TokenResponse:
    otp_manager = OTPManager(
        redis_client=redis_client,
        secret_key=bytes.fromhex(settings.otp_hmac_secret_key),
    )

    admin_id = await otp_manager.verify_challenge(
        challenge_id=payload.challenge_id,
        submitted_otp=payload.otp,
    )

    if admin_id == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )

    if admin_id == "expired":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP has expired",
        )

    if admin_id == "locked":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Maximum OTP verification attempts exceeded",
        )

    auth_manager = AuthManager(session)

    admin = await auth_manager.get_admin_by_id(admin_id)

    if admin is None or not admin.is_active or admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )

    access_token = JWTService().create_access_token(
        str(admin.id)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
