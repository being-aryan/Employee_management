from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.manager import (
    create_employee,
    delete_employee,
    get_all_employees,
    get_employee_by_id,
    search_employees,
    update_employee,
    update_employee_partial,
)
from app.schemas import CreateEmployee, Employee, EmployeeReplace, EmployeeUpdate

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.get("", response_model=list[Employee])
def get_employees() -> list[Employee]:
    return get_all_employees()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return the API health status."""
    return {"status": "ok"}


@router.get("/search", response_model=list[Employee])
def search_employee_route(
    department: str | None = None,
    status: str | None = None,
    min_salary: Annotated[float | None, Query(ge=0)] = None,
    max_salary: Annotated[float | None, Query(ge=0)] = None,
) -> list[Employee]:
    if (
            min_salary is not None
            and max_salary is not None
            and min_salary>max_salary
        ):
            raise HTTPException(
                status_code=400,
                detail="Min_salary is not greater then Max_salary",
            )
    return search_employees(
        department=department,
        status=status,
        min_salary=min_salary,
        max_salary=max_salary,
    )

@router.get("/{employee_id}", response_model=Employee)
def get_employee_by_id_route(employee_id: int) -> Employee:
    return get_employee_by_id(employee_id)


@router.post("", response_model=Employee)
def create_employee_route(employee: CreateEmployee) -> Employee:
    return create_employee(employee)


@router.put("/{employee_id}", response_model=Employee)
def update_employee_route(employee_id: int, employee: EmployeeReplace) -> Employee:
    return update_employee(employee_id, employee)


@router.patch("/{employee_id}", response_model=Employee)
def update_employee_partial_route(
    employee_id: int,
    employee_update: EmployeeUpdate,
) -> Employee:
    return update_employee_partial(employee_id, employee_update)


@router.delete("/{employee_id}", response_model=dict[str, str])
def delete_employee_route(employee_id: int) -> dict[str, str]:
    return delete_employee(employee_id)
