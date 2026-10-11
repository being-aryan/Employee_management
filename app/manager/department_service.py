from app.exceptions import DepartmentAlreadyExistError

departments: list[str]=[
    "Backend",
    "IT",
    "Sales&Marketing",
    "BA",
    "Project Manager",
]
def get_all_departement()->list[str]:
    return departments
def create_department(department: str):
    for existing_department in departments:
        if existing_department.lower()==department.lower():
            raise DepartmentAlreadyExistError(
                "Department already exists in data"
            )
    departments.append(department)
    return department
def department_exists(department: str) -> bool:
    return any(
        existing_department.lower() == department.lower()
        for existing_department in departments
    )
