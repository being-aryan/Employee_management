from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.exceptions import (
    DepartmentNotFoundError,
    EmployeeEmailAlreadyExistError,
    EmployeeNotFoundError,
)
from app.models.department import Department as DepartmentModel
from app.models.employee import Employee as EmployeeModel
from app.models.employee import EmployeeStatus as ModelEmployeeStatus
from app.schemas import (
    CreateEmployee,
    DeletedEmployee,
    Employee,
    EmployeeReplace,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)


class EmployeeManager:
    """Employee business logic backed by asynchronous PostgreSQL access."""

    @staticmethod
    async def _get_department(
        session: AsyncSession,
        name: str,
    ) -> DepartmentModel:
        normalized = name.strip()
        department = await session.scalar(
            select(DepartmentModel).where(
                func.lower(DepartmentModel.name) == normalized.lower()
            )
        )
        if department is None:
            raise DepartmentNotFoundError(f"Department '{name}' does not exist")
        return department

    @staticmethod
    async def _get_employee(
        session: AsyncSession,
        employee_id: int,
        include_deleted: bool = False,
    ) -> EmployeeModel:
        statement = (
            select(EmployeeModel)
            .options(joinedload(EmployeeModel.department))
            .where(EmployeeModel.id == employee_id)
        )
        if not include_deleted:
            statement = statement.where(EmployeeModel.is_deleted.is_(False))

        employee = await session.scalar(statement)
        if employee is None:
            raise EmployeeNotFoundError("Employee not found")
        return employee

    @staticmethod
    def _to_schema(employee: EmployeeModel) -> Employee:
        return Employee.model_validate(
            {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "department": employee.department.name,
                "salary": employee.salary,
                "status": employee.status.value,
                "is_deleted": employee.is_deleted,
            }
        )

    @staticmethod
    def _to_deleted_schema(employee: EmployeeModel) -> DeletedEmployee:
        return DeletedEmployee.model_validate(
            {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "department": employee.department.name,
                "salary": employee.salary,
                "status": employee.status.value,
                "is_deleted": employee.is_deleted,
            }
        )

    @staticmethod
    async def _check_duplicate_email(
        session: AsyncSession,
        email: str,
        exclude_employee_id: int | None = None,
    ) -> None:
        statement = select(EmployeeModel.id).where(
            func.lower(EmployeeModel.email) == email.strip().lower(),
            EmployeeModel.is_deleted.is_(False),
        )
        if exclude_employee_id is not None:
            statement = statement.where(EmployeeModel.id != exclude_employee_id)

        if await session.scalar(statement) is not None:
            raise EmployeeEmailAlreadyExistError(
                "An active employee with this email already exists"
            )

    @staticmethod
    async def _commit_employee_change(session: AsyncSession) -> None:
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            constraint_name = getattr(
                getattr(exc.orig, "diag", None),
                "constraint_name",
                None,
            )
            if constraint_name == "uq_employees_active_email":
                raise EmployeeEmailAlreadyExistError(
                    "An active employee with this email already exists"
                ) from exc
            raise

    @staticmethod
    async def _paginate(
        session: AsyncSession,
        conditions: list[Any],
        page: int,
        page_size: int,
        include_deleted: bool = False,
    ) -> dict[str, Any]:
        total = (
            await session.scalar(
                select(func.count()).select_from(EmployeeModel).where(*conditions)
            )
            or 0
        )
        total_pages = (total + page_size - 1) // page_size if total else 0

        statement = (
            select(EmployeeModel)
            .options(joinedload(EmployeeModel.department))
            .where(*conditions)
            .order_by(EmployeeModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await session.scalars(statement)
        records = result.unique().all()

        items = [
            EmployeeManager._to_deleted_schema(item)
            if include_deleted
            else EmployeeManager._to_schema(item)
            for item in records
        ]
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }

    async def get_all_employees(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        conditions = [EmployeeModel.is_deleted.is_(False)]
        return await self._paginate(session, conditions, page, page_size)

    async def get_deleted_employees(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        conditions = [EmployeeModel.is_deleted.is_(True)]
        return await self._paginate(
            session, conditions, page, page_size, include_deleted=True
        )

    async def create_employee(
        self,
        session: AsyncSession,
        employee: CreateEmployee,
    ) -> Employee:
        department = await self._get_department(session, employee.department)
        email = str(employee.email).strip().lower()
        await self._check_duplicate_email(session, email)

        new_employee = EmployeeModel(
            name=employee.name,
            email=email,
            department=department,
            salary=employee.salary,
            status=ModelEmployeeStatus(employee.status.value),
            is_deleted=False,
        )
        session.add(new_employee)
        await self._commit_employee_change(session)
        await session.refresh(new_employee, attribute_names=["department"])
        return self._to_schema(new_employee)

    async def get_employee_by_id(
        self,
        session: AsyncSession,
        employee_id: int,
    ) -> Employee:
        return self._to_schema(await self._get_employee(session, employee_id))

    async def update_employee(
        self,
        session: AsyncSession,
        employee_id: int,
        employee: EmployeeReplace,
    ) -> Employee:
        existing = await self._get_employee(session, employee_id)
        department = await self._get_department(session, employee.department)
        email = str(employee.email).strip().lower()
        await self._check_duplicate_email(session, email, employee_id)

        existing.name = employee.name
        existing.email = email
        existing.department = department
        existing.salary = employee.salary
        existing.status = ModelEmployeeStatus(employee.status.value)

        await self._commit_employee_change(session)
        await session.refresh(existing, attribute_names=["department"])
        return self._to_schema(existing)

    async def update_employee_partial(
        self,
        session: AsyncSession,
        employee_id: int,
        employee_update: EmployeeUpdate,
    ) -> Employee:
        existing = await self._get_employee(session, employee_id)
        changes = employee_update.model_dump(exclude_unset=True)

        if not changes:
            return self._to_schema(existing)

        for key, value in changes.items():
            if value is None:
                raise ValueError(f"{key.replace('_', ' ').capitalize()} cannot be null")

        if "department" in changes:
            existing.department = await self._get_department(
                session, changes.pop("department")
            )

        if "email" in changes:
            email = str(changes["email"]).strip().lower()
            await self._check_duplicate_email(session, email, employee_id)
            changes["email"] = email

        for key, value in changes.items():
            if key == "status":
                value = ModelEmployeeStatus(value.value)
            setattr(existing, key, value)

        await self._commit_employee_change(session)
        await session.refresh(existing, attribute_names=["department"])
        return self._to_schema(existing)

    async def update_employee_status(
        self,
        session: AsyncSession,
        employee_id: int,
        status_update: EmployeeStatusUpdate,
    ) -> Employee:
        employee = await self._get_employee(session, employee_id)
        employee.status = ModelEmployeeStatus(status_update.status.value)
        await session.commit()
        await session.refresh(employee, attribute_names=["department"])
        return self._to_schema(employee)

    async def delete_employee(
        self,
        session: AsyncSession,
        employee_id: int,
    ) -> Employee:
        employee = await self._get_employee(session, employee_id)
        employee.is_deleted = True
        await session.commit()
        await session.refresh(employee, attribute_names=["department"])
        return self._to_schema(employee)

    async def restore_employee(
        self,
        session: AsyncSession,
        employee_id: int,
    ) -> Employee:
        employee = await self._get_employee(
            session,
            employee_id,
            include_deleted=True,
        )
        if not employee.is_deleted:
            raise EmployeeNotFoundError("Deleted employee not found")

        await self._check_duplicate_email(session, employee.email, employee_id)
        employee.is_deleted = False
        await self._commit_employee_change(session)
        await session.refresh(employee, attribute_names=["department"])
        return self._to_schema(employee)

    async def search_employees(
        self,
        session: AsyncSession,
        query: str,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        query = query.strip()
        if not query:
            conditions = [EmployeeModel.id == -1]
        else:
            pattern = f"%{query}%"
            conditions = [
                EmployeeModel.is_deleted.is_(False),
                (
                    EmployeeModel.name.ilike(pattern)
                    | EmployeeModel.email.ilike(pattern)
                    | EmployeeModel.department.has(DepartmentModel.name.ilike(pattern))
                ),
            ]
        return await self._paginate(session, conditions, page, page_size)

    async def filter_employees(
        self,
        session: AsyncSession,
        department: str | None = None,
        status: Any | None = None,
        min_salary: float | None = None,
        max_salary: float | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if (
            min_salary is not None
            and max_salary is not None
            and min_salary > max_salary
        ):
            raise ValueError("min_salary cannot be greater than max_salary")

        conditions = [EmployeeModel.is_deleted.is_(False)]
        if department is not None:
            conditions.append(
                EmployeeModel.department.has(
                    func.lower(DepartmentModel.name) == department.strip().lower()
                )
            )
        if status is not None:
            conditions.append(EmployeeModel.status == ModelEmployeeStatus(status.value))
        if min_salary is not None:
            conditions.append(EmployeeModel.salary >= min_salary)
        if max_salary is not None:
            conditions.append(EmployeeModel.salary <= max_salary)

        return await self._paginate(session, conditions, page, page_size)
