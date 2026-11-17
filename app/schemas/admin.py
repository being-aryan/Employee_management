from typing import Literal

from pydantic import BaseModel, EmailStr, Field

AdminRole = Literal["admin"]


class Admin(BaseModel):
    id: int = Field(ge=1)
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    role: AdminRole


class AdminLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class OTPVerificationRequest(BaseModel):
    challenge_id: str = Field(min_length=1)
    otp: str = Field(pattern=r"^\d{6}$")


class OTPChallengeResponse(BaseModel):
    message: str
    challenge_id: str
    expires_in: int
