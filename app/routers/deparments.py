from fastapi import APIRouter

from app.manager import create_department, get_all_departement

router = APIRouter(
    prefix="/departments",
    tags=["Department"],
)

@router.get("", response_model=list[str])
def get_departments()-> list[str]:
    return get_all_departement()
@router.post("")
def create_deparment_data(deparment:str)->str:
    return create_department(deparment)
