from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.admin import Admin as AdminModel
from app.security import PasswordService


class AuthManager:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.password_service = PasswordService()

    async def authenticate_admin(
        self,
        email: str,
        password: str,
    ) -> AdminModel | None:
        normalized_email = email.strip().lower()

        statement = select(AdminModel).where(
            func.lower(AdminModel.email) == normalized_email
        )

        admin = await self.session.scalar(statement)

        if admin is None or not admin.is_active:
            return None

        password_is_valid = await run_in_threadpool(
            self.password_service.verify_password,
            password,
            admin.hashed_password,
        )
        if not password_is_valid:
            return None

        return admin

    async def get_admin_by_id(self, admin_id: int) -> AdminModel | None:
        return await self.session.get(AdminModel, admin_id)
