from fastapi import APIRouter

from app.managers import department_manager

router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


@router.get("")
def get_departments() -> list[str]:
    return department_manager.get_all_departement()


@router.post("")
def create_department_route(department: str) -> str:
    return department_manager.create_department(department)
