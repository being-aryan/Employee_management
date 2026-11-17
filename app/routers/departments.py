from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_dependencies import get_db
from app.managers.department_service import DepartmentManager

router = APIRouter(prefix="/departments", tags=["Departments"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("")
async def get_departments(session: DatabaseSession) -> list[str]:
    return await DepartmentManager().get_all_departments(session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_department_route(
    department: str,
    session: DatabaseSession,
) -> str:
    try:
        return await DepartmentManager().create_department(session, department)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
