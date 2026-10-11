from app.exceptions import (
    DepartmentNotFoundError,
    EmployeeEmailAlreadyExistError,
    EmployeeNotFoundError,
)
from app.manager.department_service import department_exists
from app.schemas import CreateEmployee, Employee, EmployeeReplace, EmployeeUpdate

employees: list[Employee] = []
next_employee_id = 1


def get_all_employees() -> list[Employee]:
    return employees


def create_employee(employee: CreateEmployee) -> Employee:
    if not department_exists(employee.department):
        raise DepartmentNotFoundError(
            f"Department '{employee.department}' does not exist"
    )
    for existing_employee in employees:
        if existing_employee.email == employee.email:
            raise EmployeeEmailAlreadyExistError(
                "Employee with this email already exists"
        )
    employee_data = employee.model_dump()
    global next_employee_id
    new_employee = Employee(
        id=next_employee_id,
        **employee_data,
    )
    next_employee_id += 1
    employees.append(new_employee)
    return new_employee


def get_employee_by_id(employee_id: int) -> Employee:
    for employee in employees:
        if employee.id == employee_id:
            return employee
    raise EmployeeNotFoundError("Employee Not Found")


def update_employee(
    employee_id: int,
    employee: EmployeeReplace,
) -> Employee:
    if not department_exists(employee.department):
        raise DepartmentNotFoundError(
            f"Department '{employee.department}' does not exist"
        )

    for index, existing_employee in enumerate(employees):
        if existing_employee.id == employee_id:
            updated_employee = Employee(
                id=employee_id,
                **employee.model_dump(),
            )
            employees[index] = updated_employee
            return updated_employee

    raise EmployeeNotFoundError("Employee not found")


def update_employee_partial(
    employee_id: int,
    employee_update: EmployeeUpdate,
) -> Employee:
    for existing_employee in employees:
        if existing_employee.id == employee_id:
            update_data = employee_update.model_dump(exclude_unset=True)
            if "department" in update_data:
                 if not department_exists(update_data["department"]):
                    raise DepartmentNotFoundError(
                         f"Department '{update_data['department']}' does not exist"
        )
            for key, value in update_data.items():
                setattr(existing_employee, key, value)
            return existing_employee
    raise EmployeeNotFoundError("Employee Not Found")


def delete_employee(employee_id: int) -> dict[str, str]:
    for existing_employee in employees:
        if existing_employee.id == employee_id:
            employees.remove(existing_employee)
            return {"message": "Employee deleted successfully."}
    raise EmployeeNotFoundError("Employee Not Found")


def search_employees(
    department: str | None = None,
    status: str | None = None,
    min_salary: float | None = None,
    max_salary: float | None = None,
) -> list[Employee]:
    filtered_employees = employees
    if department is not None:
        filtered_employees = [
            employee
            for employee in filtered_employees
            if employee.department.lower() == department.lower()
        ]
    if status is not None:
        filtered_employees = [
            employee
            for employee in filtered_employees
            if employee.status == status
        ]
    if min_salary is not None:
        filtered_employees = [
            employee
            for employee in filtered_employees
            if employee.salary >= min_salary
        ]
    if max_salary is not None:
        filtered_employees = [
            employee
            for employee in filtered_employees
            if employee.salary <= max_salary
        ]
    return filtered_employees
