from app.exceptions import (
    DepartmentNotFoundError,
    EmployeeEmailAlreadyExistError,
    EmployeeNotFoundError,
)
from app.managers.department_service import DepartmentManager
from app.schemas import (
    CreateEmployee,
    Employee,
    EmployeeReplace,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)


class EmployeeManager:
    def __init__(self, department_manager: DepartmentManager) -> None:
        self.employees: list[Employee] = []
        self.next_employee_id = 1
        self.department_manager = department_manager

    def get_all_employees(self) -> list[Employee]:
        return self.employees

    def create_employee(self, employee: CreateEmployee) -> Employee:
        if not self.department_manager.department_exists(employee.department):
            raise DepartmentNotFoundError(
                f"Department '{employee.department}' does not exist"
            )

        for existing_employee in self.employees:
            if existing_employee.email == employee.email:
                raise EmployeeEmailAlreadyExistError(
                    "Employee with this email already exists"
                )

        employee_data = employee.model_dump()

        new_employee = Employee(
            id=self.next_employee_id,
            **employee_data,
        )

        self.next_employee_id += 1
        self.employees.append(new_employee)

        return new_employee

    def get_employee_by_id(self, employee_id: int) -> Employee:
        for employee in self.employees:
            if employee.id == employee_id:
                return employee

        raise EmployeeNotFoundError("Employee not found")

    def update_employee(
        self,
        employee_id: int,
        employee: EmployeeReplace,
    ) -> Employee:
        if not self.department_manager.department_exists(employee.department):
            raise DepartmentNotFoundError(
                f"Department '{employee.department}' does not exist"
            )

        for index, existing_employee in enumerate(self.employees):
            if existing_employee.id == employee_id:
                updated_employee = Employee(
                    id=employee_id,
                    **employee.model_dump(),
                )

                self.employees[index] = updated_employee
                return updated_employee

        raise EmployeeNotFoundError("Employee not found")

    def update_employee_partial(
        self,
        employee_id: int,
        employee_update: EmployeeUpdate,
    ) -> Employee:
        for existing_employee in self.employees:
            if existing_employee.id == employee_id:
                update_data = employee_update.model_dump(exclude_unset=True)

                if "department" in update_data:
                    department = update_data["department"]

                    if department is None:
                        raise ValueError("Department cannot be null")

                    if not self.department_manager.department_exists(department):
                        raise DepartmentNotFoundError(
                            f"Department '{department}' does not exist"
                        )

                for key, value in update_data.items():
                    setattr(existing_employee, key, value)

                return existing_employee

        raise EmployeeNotFoundError("Employee not found")

    def update_employee_status(
        self,
        employee_id: int,
        status_update: EmployeeStatusUpdate,
    ) -> Employee:
        for employee in self.employees:
            if employee.id == employee_id:
                employee.status = status_update.status
                return employee

        raise EmployeeNotFoundError("Employee not found")

    def delete_employee(self, employee_id: int) -> dict[str, str]:
        for employee in self.employees:
            if employee.id == employee_id:
                self.employees.remove(employee)
                return {"message": "Employee deleted successfully."}

        raise EmployeeNotFoundError("Employee not found")

    def search_employees(
        self,
        department: str | None = None,
        status: str | None = None,
        min_salary: float | None = None,
        max_salary: float | None = None,
    ) -> list[Employee]:
        filtered_employees = self.employees

        if department is not None:
            filtered_employees = [
                employee
                for employee in filtered_employees
                if employee.department.lower() == department.lower()
            ]

        if status is not None:
            filtered_employees = [
                employee for employee in filtered_employees if employee.status == status
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
