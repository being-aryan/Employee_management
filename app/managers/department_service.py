from app.exceptions import DepartmentAlreadyExistError


class DepartmentManager:
    def __init__(self) -> None:
        self.departments: list[str] = [
            "Backend",
            "IT",
            "Sales&Marketing",
            "BA",
            "Project Manager",
        ]

    def get_all_departement(self) -> list[str]:
        return self.departments

    def create_department(self, department: str) -> str:
        for existing_department in self.departments:
            if existing_department.lower() == department.lower():
                raise DepartmentAlreadyExistError("Department already exists in data")

        self.departments.append(department)
        return department

    def department_exists(self, department: str) -> bool:
        return any(
            existing_department.lower() == department.lower()
            for existing_department in self.departments
        )
