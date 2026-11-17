from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_dependencies import get_db
from app.managers.employee_service import EmployeeManager
from app.schemas import (
    APIResponse,
    CreateEmployee,
    Employee,
    EmployeeReplace,
    EmployeeStatus,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)

router = APIRouter(prefix="/employees", tags=["Employees"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "",
    response_model=APIResponse[Employee],
    status_code=http_status.HTTP_201_CREATED,
)
async def create_employee(
    employee: CreateEmployee,
    session: DatabaseSession,
) -> APIResponse[Employee]:
    data = await EmployeeManager().create_employee(session, employee)
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_201_CREATED,
        message="Employee created successfully",
        data=data,
    )


@router.get(
    "",
    response_model=APIResponse[dict],
    response_model_exclude={"data": {"items": {"__all__": {"is_deleted"}}}},
)
async def get_all_employees(
    session: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> APIResponse[dict]:
    data = await EmployeeManager().get_all_employees(session, page, page_size)
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employees fetched successfully",
        data=data,
    )


@router.get(
    "/search",
    response_model=APIResponse[dict],
    response_model_exclude={"data": {"items": {"__all__": {"is_deleted"}}}},
)
async def search_employees(
    session: DatabaseSession,
    q: Annotated[str, Query(min_length=1, max_length=100)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> APIResponse[dict]:
    data = await EmployeeManager().search_employees(session, q, page, page_size)
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee search completed successfully",
        data=data,
    )


@router.get(
    "/filter",
    response_model=APIResponse[dict],
    response_model_exclude={"data": {"items": {"__all__": {"is_deleted"}}}},
)
async def filter_employees(
    session: DatabaseSession,
    department: str | None = None,
    status: EmployeeStatus | None = None,
    min_salary: Annotated[float | None, Query(ge=0)] = None,
    max_salary: Annotated[float | None, Query(ge=0)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> APIResponse[dict]:
    try:
        data = await EmployeeManager().filter_employees(
            session,
            department=department,
            status=status,
            min_salary=min_salary,
            max_salary=max_salary,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employees filtered successfully",
        data=data,
    )


@router.get("/deleted", response_model=APIResponse[dict])
async def get_deleted_employees(
    session: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> APIResponse[dict]:
    data = await EmployeeManager().get_deleted_employees(session, page, page_size)
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Deleted employees retrieved successfully",
        data=data,
    )


@router.patch(
    "/{employee_id}/restore",
    response_model=APIResponse[Employee],
)
async def restore_employee(
    employee_id: int,
    session: DatabaseSession,
) -> APIResponse[Employee]:
    data = await EmployeeManager().restore_employee(session, employee_id)
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee restored successfully",
        data=data,
    )


@router.patch(
    "/{employee_id}/status",
    response_model=APIResponse[Employee],
)
async def update_employee_status(
    employee_id: int,
    status_update: EmployeeStatusUpdate,
    session: DatabaseSession,
) -> APIResponse[Employee]:
    data = await EmployeeManager().update_employee_status(
        session,
        employee_id,
        status_update,
    )
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee status updated successfully",
        data=data,
    )


@router.get("/{employee_id}", response_model=APIResponse[Employee])
async def get_employee_by_id(
    employee_id: int,
    session: DatabaseSession,
) -> APIResponse[Employee]:
    data = await EmployeeManager().get_employee_by_id(session, employee_id)
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee retrieved successfully",
        data=data,
    )


@router.put("/{employee_id}", response_model=APIResponse[Employee])
async def update_employee(
    employee_id: int,
    employee: EmployeeReplace,
    session: DatabaseSession,
) -> APIResponse[Employee]:
    data = await EmployeeManager().update_employee(session, employee_id, employee)
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee replaced successfully",
        data=data,
    )


@router.patch("/{employee_id}", response_model=APIResponse[Employee])
async def update_employee_partial(
    employee_id: int,
    employee_update: EmployeeUpdate,
    session: DatabaseSession,
) -> APIResponse[Employee]:
    try:
        data = await EmployeeManager().update_employee_partial(
            session,
            employee_id,
            employee_update,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee updated successfully",
        data=data,
    )


@router.delete(
    "/{employee_id}",
    response_model=APIResponse[Employee],
    response_model_exclude={"data": {"is_deleted"}},
)
async def delete_employee(
    employee_id: int,
    session: DatabaseSession,
) -> APIResponse[Employee]:
    data = await EmployeeManager().delete_employee(session, employee_id)
    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee soft-deleted successfully",
        data=data,
    )
