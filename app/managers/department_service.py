from app.exceptions import DepartmentAlreadyExistError
from app.storage.json_storage import read_json, write_json

DEFAULT_DEPARTMENTS: list[str] = [
    "Backend",
    "IT",
    "Sales&Marketing",
    "BA",
    "Project Manager",
]


class DepartmentManager:
    def __init__(self) -> None:
        self.departments: list[str] = read_json(
            "departments.json",
            DEFAULT_DEPARTMENTS,
        )

    def get_all_departement(self) -> list[str]:
        return self.departments

    def create_department(self, department: str) -> str:
        for existing_department in self.departments:
            if existing_department.lower() == department.lower():
                raise DepartmentAlreadyExistError("Department already exists in data")

        self.departments.append(department)

        write_json("departments.json", self.departments)

        return department

    def department_exists(self, department: str) -> bool:
        return any(
            existing_department.lower() == department.lower()
            for existing_department in self.departments
        )
