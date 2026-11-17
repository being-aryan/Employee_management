from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings


class JWTService:
    def __init__(self) -> None:
        self.secret_key = settings.jwt_secret_key
        self.algorithm = "HS256"
        self.expires_minutes = settings.jwt_access_token_expire_minutes

    def create_access_token(self, subject: str) -> str:
        now = datetime.now(UTC)

        payload = {
            "sub": subject,
            "iat": now,
            "exp": now + timedelta(minutes=self.expires_minutes),
        }

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

    def verify_access_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={"require": ["sub", "exp"], "verify_signature": True},
        )


jwt_service = JWTService()
