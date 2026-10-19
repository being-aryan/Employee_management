from app.exceptions import (
    DepartmentNotFoundError,
    EmployeeEmailAlreadyExistError,
    EmployeeNotFoundError,
)
from app.managers.department_service import DepartmentManager
from app.schemas import (
    CreateEmployee,
    DeletedEmployee,
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
        "is_deleted": False,
    },
    {
        "id": 2,
        "name": "Priya Verma",
        "email": "priya@example.com",
        "department": "IT",
        "salary": 550000,
        "status": "active",
        "is_deleted": False,
    },
    {
        "id": 3,
        "name": "Rahul Singh",
        "email": "rahul@example.com",
        "department": "BA",
        "salary": 450000,
        "status": "on_leave",
        "is_deleted": False,
    },
]


class EmployeeManager:
    def __init__(
        self,
        department_manager: DepartmentManager,
    ) -> None:
        employee_data = read_json(
            "employees.json",
            DEFAULT_EMPLOYEES,
        )

        self.employees: list[Employee] = [
            Employee.model_validate(
                {
                    **item,
                    "is_deleted": item.get("is_deleted", False),
                }
            )
            for item in employee_data
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

    def _get_active_employee(
        self,
        employee_id: int,
    ) -> Employee:
        for employee in self.employees:
            if employee.id == employee_id and not employee.is_deleted:
                return employee

        raise EmployeeNotFoundError("Employee not found")

    def get_all_employees(self) -> list[Employee]:
        return [employee for employee in self.employees if not employee.is_deleted]

    def get_deleted_employees(self) -> list[DeletedEmployee]:
        return [
            DeletedEmployee.model_validate(employee.model_dump(mode="json"))
            for employee in self.employees
            if employee.is_deleted
        ]

    def create_employee(
        self,
        employee: CreateEmployee,
    ) -> Employee:
        if not self.department_manager.department_exists(employee.department):
            raise DepartmentNotFoundError(
                f"Department '{employee.department}' does not exist"
            )

        email = str(employee.email).casefold()

        for existing_employee in self.employees:
            if existing_employee.is_deleted:
                continue

            if existing_employee.email.casefold() == email:
                raise EmployeeEmailAlreadyExistError(
                    "An active employee with this email already exists"
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

    def get_employee_by_id(
        self,
        employee_id: int,
    ) -> Employee:
        return self._get_active_employee(employee_id)

    def update_employee(
        self,
        employee_id: int,
        employee: EmployeeReplace,
    ) -> Employee:
        existing_employee = self._get_active_employee(employee_id)

        if not self.department_manager.department_exists(employee.department):
            raise DepartmentNotFoundError(
                f"Department '{employee.department}' does not exist"
            )

        email = str(employee.email).casefold()

        for other_employee in self.employees:
            if (
                other_employee.id != employee_id
                and not other_employee.is_deleted
                and other_employee.email.casefold() == email
            ):
                raise EmployeeEmailAlreadyExistError(
                    "Employee with this email already exists"
                )
        updated_employee = Employee(
            id=employee_id,
            **employee.model_dump(),
            is_deleted=existing_employee.is_deleted,
        )

        index = self.employees.index(existing_employee)
        self.employees[index] = updated_employee
        self._save_employees()

        return updated_employee

    def update_employee_partial(
        self,
        employee_id: int,
        employee_update: EmployeeUpdate,
    ) -> Employee:
        employee_to_update = self._get_active_employee(employee_id)

        update_data = employee_update.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            return employee_to_update

        for field_name, field_value in update_data.items():
            if field_value is None:
                field_label = field_name.replace("_", " ").capitalize()
                raise ValueError(f"{field_label} cannot be null")

        if "department" in update_data:
            department = update_data["department"]

            if not self.department_manager.department_exists(department):
                raise DepartmentNotFoundError(
                    f"Department '{department}' does not exist"
                )

        if "email" in update_data:
            email = str(update_data["email"]).casefold()

            for other_employee in self.employees:
                if (
                    other_employee.id != employee_id
                    and not other_employee.is_deleted
                    and other_employee.email.casefold() == email
                ):
                    raise EmployeeEmailAlreadyExistError(
                        "Employee with this email already exists"
                    )

        updated_data = employee_to_update.model_dump()
        updated_data.update(update_data)
        updated_data["is_deleted"] = False

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
        employee = self._get_active_employee(employee_id)

        updated_employee = employee.model_copy(
            update={"status": status_update.status},
        )

        index = self.employees.index(employee)
        self.employees[index] = updated_employee
        self._save_employees()

        return updated_employee

    def delete_employee(self, employee_id: int) -> Employee:
        employee = self._get_active_employee(employee_id)

        index = self.employees.index(employee)
        deleted_employee = employee.model_copy(update={"is_deleted": True})

        self.employees[index] = deleted_employee
        self._save_employees()

        return deleted_employee

    def restore_employee(
        self,
        employee_id: int,
    ) -> Employee:
        for index, employee in enumerate(self.employees):
            if employee.id != employee_id or not employee.is_deleted:
                continue

            # Do not restore if another active employee uses this email.
            for other_employee in self.employees:
                if (
                    other_employee.id != employee_id
                    and not other_employee.is_deleted
                    and other_employee.email.casefold() == employee.email.casefold()
                ):
                    raise EmployeeEmailAlreadyExistError(
                        "An active employee already uses this email"
                    )

            restored_employee = employee.model_copy(
                update={"is_deleted": False},
            )

            self.employees[index] = restored_employee
            self._save_employees()

            return restored_employee

        raise EmployeeNotFoundError("Deleted employee not found")

    def filter_employees(
        self,
        department: str | None = None,
        status: str | None = None,
        min_salary: float | None = None,
        max_salary: float | None = None,
    ) -> list[Employee]:
        if (
            min_salary is not None
            and max_salary is not None
            and min_salary > max_salary
        ):
            raise ValueError("min_salary cannot be greater than max_salary")

        filtered_employees = self.get_all_employees()

        if department is not None:
            filtered_employees = [
                employee
                for employee in filtered_employees
                if employee.department.casefold() == department.casefold()
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

    def search_employees(
        self,
        query: str,
    ) -> list[Employee]:
        query = query.strip().casefold()

        if not query:
            return []

        matching_employees = []

        for employee in self.get_all_employees():
            searchable_fields = (
                employee.name,
                str(employee.email),
                employee.department,
            )

            if any(query in value.casefold() for value in searchable_fields):
                matching_employees.append(employee)

        return matching_employees
