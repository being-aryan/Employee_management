from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Employee Management API"
    environment: str = "development"

    database_url: str = Field(min_length=1)
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = Field(min_length=32)
    jwt_access_token_expire_minutes: int = Field(default=15, gt=0)
    jwt_refresh_token_expire_days: int = Field(default=7, gt=0)
    otp_hmac_secret_key: str = Field(min_length=64)

    cors_allowed_origins: str = "http://localhost:3000"

    @field_validator("database_url", mode="before")
    @classmethod
    def use_async_postgresql_driver(cls, value: str) -> str:
        """Normalize PostgreSQL URLs to SQLAlchemy's asyncpg dialect."""
        if not isinstance(value, str):
            return value

        replacements = (
            ("postgresql+psycopg://", "postgresql+asyncpg://"),
            ("postgresql+psycopg2://", "postgresql+asyncpg://"),
            ("postgresql://", "postgresql+asyncpg://"),
            ("postgres://", "postgresql+asyncpg://"),
        )
        for old_prefix, new_prefix in replacements:
            if value.startswith(old_prefix):
                return value.replace(old_prefix, new_prefix, 1)
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
