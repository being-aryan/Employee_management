from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi import (
    status as http_status,
)

from app.dependencies import get_current_admin
from app.managers import employee_manager
from app.schemas import (
    APIResponse,
    CreateEmployee,
    DeletedEmployee,
    Employee,
    EmployeeReplace,
    EmployeeStatus,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    dependencies=[Depends(get_current_admin)],
)


@router.post(
    "",
    response_model=APIResponse[Employee],
    status_code=http_status.HTTP_201_CREATED,
)
def create_employee(
    employee: CreateEmployee,
) -> APIResponse[Employee]:
    created_employee = employee_manager.create_employee(employee)

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_201_CREATED,
        message="Employee created successfully",
        data=created_employee,
    )


@router.get(
    "",
    response_model=APIResponse[list[Employee]],
    response_model_exclude={"data": {"__all__": {"is_deleted"}}},
)
def get_all_employees():
    employees = employee_manager.get_all_employees()

    return APIResponse(
        status_code=200,
        message="Employees fetched successfully",
        data=employees,
    )


@router.get(
    "/search",
    response_model=APIResponse[list[Employee]],
)
def search_employees(
    q: Annotated[str, Query(min_length=1, max_length=100)],
) -> APIResponse[list[Employee]]:
    employees = employee_manager.search_employees(q)

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee search completed successfully",
        data=employees,
    )


@router.get(
    "/filter",
    response_model=APIResponse[list[Employee]],
)
def filter_employees(
    department: str | None = None,
    status: EmployeeStatus | None = None,
    min_salary: Annotated[float | None, Query(ge=0)] = None,
    max_salary: Annotated[float | None, Query(ge=0)] = None,
) -> APIResponse[list[Employee]]:
    if min_salary is not None and max_salary is not None and min_salary > max_salary:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="min_salary cannot be greater than max_salary",
        )

    employees = employee_manager.filter_employees(
        department=department,
        status=status,
        min_salary=min_salary,
        max_salary=max_salary,
    )

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employees filtered successfully",
        data=employees,
    )


@router.get(
    "/deleted",
    response_model=APIResponse[list[DeletedEmployee]],
)
def get_deleted_employees() -> APIResponse[list[DeletedEmployee]]:
    employees = employee_manager.get_deleted_employees()

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Deleted employees retrieved successfully",
        data=employees,
    )


@router.patch(
    "/{employee_id}/restore",
    response_model=APIResponse[Employee],
)
def restore_employee(employee_id: int) -> APIResponse[Employee]:
    employee = employee_manager.restore_employee(employee_id)

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee restored successfully",
        data=employee,
    )


@router.patch(
    "/{employee_id}/status",
    response_model=APIResponse[Employee],
)
def update_employee_status(
    employee_id: int,
    status_update: EmployeeStatusUpdate,
) -> APIResponse[Employee]:
    employee = employee_manager.update_employee_status(
        employee_id,
        status_update,
    )

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee status updated successfully",
        data=employee,
    )


@router.get(
    "/{employee_id}",
    response_model=APIResponse[Employee],
)
def get_employee_by_id(
    employee_id: int,
) -> APIResponse[Employee]:
    employee = employee_manager.get_employee_by_id(employee_id)

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee retrieved successfully",
        data=employee,
    )


@router.put(
    "/{employee_id}",
    response_model=APIResponse[Employee],
)
def update_employee(
    employee_id: int,
    employee: EmployeeReplace,
) -> APIResponse[Employee]:
    updated_employee = employee_manager.update_employee(
        employee_id,
        employee,
    )

    return APIResponse(
        success=True,
        status_code=http_status.HTTP_200_OK,
        message="Employee replaced successfully",
        data=updated_employee,
    )


@router.patch(
    "/{employee_id}",
    response_model=APIResponse[Employee],
)
def update_employee_partial(
    employee_id: int,
    employee_update: EmployeeUpdate,
) -> APIResponse[Employee]:
    try:
        employee = employee_manager.update_employee_partial(
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
        data=employee,
    )


@router.delete(
    "/{employee_id}",
    response_model=APIResponse[Employee],
    response_model_exclude={"data": {"is_deleted"}},
)
def delete_employee(employee_id: int):
    deleted_employee = employee_manager.delete_employee(employee_id)

    return APIResponse(
        status_code=200,
        message="Employee soft-deleted successfully",
        data=deleted_employee,
    )
