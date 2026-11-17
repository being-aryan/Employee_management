from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DepartmentAlreadyExistError
from app.models import Department


class DepartmentManager:
    async def get_all_departments(self, session: AsyncSession) -> list[str]:
        statement = select(Department.name).order_by(Department.id)
        result = await session.scalars(statement)
        return list(result.all())

    async def create_department(
        self,
        session: AsyncSession,
        department: str,
    ) -> str:
        department = department.strip()
        if not department:
            raise ValueError("Department name cannot be empty")

        statement = select(Department.id).where(
            func.lower(Department.name) == department.lower()
        )
        if await session.scalar(statement) is not None:
            raise DepartmentAlreadyExistError("Department already exists")

        session.add(Department(name=department))
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise DepartmentAlreadyExistError("Department already exists") from exc

        return department

    async def department_exists(
        self,
        session: AsyncSession,
        department: str,
    ) -> bool:
        statement = select(Department.id).where(
            func.lower(Department.name) == department.strip().lower()
        )
        return await session.scalar(statement) is not None
