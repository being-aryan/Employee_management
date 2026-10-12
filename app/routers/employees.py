from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.managers import employee_manager
from app.schemas import (
    CreateEmployee,
    Employee,
    EmployeeReplace,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.get("/health")
def employee_health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("", response_model=Employee)
def create_employee(employee: CreateEmployee) -> Employee:
    return employee_manager.create_employee(employee)


@router.get("", response_model=list[Employee])
def get_all_employees() -> list[Employee]:
    return employee_manager.get_all_employees()


@router.get("/search", response_model=list[Employee])
def search_employees(
    department: str | None = None,
    status: str | None = None,
    min_salary: Annotated[float | None, Query(ge=0)] = None,
    max_salary: Annotated[float | None, Query(ge=0)] = None,
) -> list[Employee]:
    if min_salary is not None and max_salary is not None and min_salary > max_salary:
        raise HTTPException(
            status_code=400,
            detail="min_salary cannot be greater than max_salary",
        )

    return employee_manager.search_employees(
        department=department,
        status=status,
        min_salary=min_salary,
        max_salary=max_salary,
    )


@router.patch("/{employee_id}/status", response_model=Employee)
def update_employee_status(
    employee_id: int,
    status_update: EmployeeStatusUpdate,
) -> Employee:
    return employee_manager.update_employee_status(
        employee_id,
        status_update,
    )


@router.get("/{employee_id}", response_model=Employee)
def get_employee_by_id(employee_id: int) -> Employee:
    return employee_manager.get_employee_by_id(employee_id)


@router.put("/{employee_id}", response_model=Employee)
def update_employee(
    employee_id: int,
    employee: EmployeeReplace,
) -> Employee:
    return employee_manager.update_employee(employee_id, employee)


@router.patch("/{employee_id}", response_model=Employee)
def update_employee_partial(
    employee_id: int,
    employee_update: EmployeeUpdate,
) -> Employee:
    return employee_manager.update_employee_partial(
        employee_id,
        employee_update,
    )


@router.delete("/{employee_id}")
def delete_employee(employee_id: int) -> dict[str, str]:
    return employee_manager.delete_employee(employee_id)
