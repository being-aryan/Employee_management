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
from app.storage.json_storage import read_json, write_json

DEFAULT_EMPLOYEES: list[dict[str, object]] = [
    {
        "id": 1,
        "name": "Aarav Sharma",
        "email": "aarav@example.com",
        "department": "Backend",
        "salary": 600000,
        "status": "active",
    },
    {
        "id": 2,
        "name": "Priya Verma",
        "email": "priya@example.com",
        "department": "IT",
        "salary": 550000,
        "status": "active",
    },
    {
        "id": 3,
        "name": "Rahul Singh",
        "email": "rahul@example.com",
        "department": "BA",
        "salary": 450000,
        "status": "on_leave",
    },
]


class EmployeeManager:
    def __init__(self, department_manager: DepartmentManager) -> None:
        employee_data = read_json("employees.json", DEFAULT_EMPLOYEES)

        self.employees: list[Employee] = [
            Employee.model_validate(item) for item in employee_data
        ]

        self.next_employee_id = (
            max(
                (employee.id for employee in self.employees),
                default=0,
            )
            + 1
        )

        self.department_manager = department_manager

    def _save_employees(self) -> None:
        employee_data = [
            employee.model_dump(mode="json") for employee in self.employees
        ]
        write_json("employees.json", employee_data)

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

        self.employees.append(new_employee)
        self.next_employee_id += 1
        self._save_employees()

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
                for other_employee in self.employees:
                    if (
                        other_employee.id != employee_id
                        and other_employee.email.lower() == employee.email.lower()
                    ):
                        raise EmployeeEmailAlreadyExistError(
                            "Employee with this email already exists"
                        )

                updated_employee = Employee(
                    id=employee_id,
                    **employee.model_dump(),
                )
                self.employees[index] = updated_employee
                self._save_employees()

                return updated_employee

        raise EmployeeNotFoundError("Employee not found")

    def update_employee_partial(
        self,
        employee_id: int,
        employee_update: EmployeeUpdate,
    ) -> Employee:
        employee_to_update = next(
            (employee for employee in self.employees if employee.id == employee_id),
            None,
        )

        if employee_to_update is None:
            raise EmployeeNotFoundError("Employee not found")

        update_data = employee_update.model_dump(exclude_unset=True)

        if not update_data:
            return employee_to_update
        for field_name, field_value in update_data.items():
            if field_value is None:
                raise ValueError(
                    f"{field_name.replace('_', ' ').capitalize()} cannot be null"
                )

        if "department" in update_data:
            department = update_data["department"]

            if not self.department_manager.department_exists(department):
                raise DepartmentNotFoundError(
                    f"Department '{department}' does not exist"
                )

        if "email" in update_data:
            email = update_data["email"]

            for other_employee in self.employees:
                if (
                    other_employee.id != employee_id
                    and other_employee.email.lower() == email.lower()
                ):
                    raise EmployeeEmailAlreadyExistError(
                        "Employee with this email already exists"
                    )

        updated_data = employee_to_update.model_dump()
        updated_data.update(update_data)

        updated_employee = Employee.model_validate(updated_data)

        index = self.employees.index(employee_to_update)
        self.employees[index] = updated_employee

        self._save_employees()

        return updated_employee

    def update_employee_status(
        self,
        employee_id: int,
        status_update: EmployeeStatusUpdate,
    ) -> Employee:
        for index, employee in enumerate(self.employees):
            if employee.id == employee_id:
                updated_employee = employee.model_copy(
                    update={"status": status_update.status}
                )
                self.employees[index] = updated_employee
                self._save_employees()

                return updated_employee

        raise EmployeeNotFoundError("Employee not found")

    def delete_employee(self, employee_id: int) -> dict[str, str]:
        for employee in self.employees:
            if employee.id == employee_id:
                self.employees.remove(employee)
                self._save_employees()

                return {"message": "Employee deleted successfully."}

        raise EmployeeNotFoundError("Employee not found")

    def filter_employees(
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
    

    def search_employees(self, query: str) -> list[Employee]:

        query = query.strip().casefold()

        if not query:
            return []

        matching_employees = []

        for employee in self.employees:
            searchable_fields = (
                employee.name,
                employee.email,
                employee.department,
            )

            if any(
                query in str(value).casefold()
                for value in searchable_fields
                if value is not None
            ):
                matching_employees.append(employee)

        return matching_employees
