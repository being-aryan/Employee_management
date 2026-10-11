from typing import Literal

from pydantic import BaseModel, EmailStr, Field

EmployeeStatus=Literal["active", "inactive", "on-leave"]
class Employee(BaseModel):
    id: int = Field(ge=1)
    name: str = Field(min_length=2)
    email: EmailStr
    department: str = Field(min_length=2)
    salary: float = Field(ge=0)
    status: EmployeeStatus

class EmployeeStatusUpdate(BaseModel):
    status: EmployeeStatus

class EmployeeUpdate(BaseModel):
    name: str | None = Field(min_length=2)
    email: EmailStr | None = None
    department: str | None = Field(min_length=2)
    salary: float | None = None
    status: EmployeeStatus | None=None


class CreateEmployee(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    department: str = Field(min_length=2)
    salary: float = Field(ge=0)
    status: Literal["active", "inactive", "on-leave"]


class EmployeeReplace(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    department: str = Field(min_length=2)
    salary: float = Field(ge=0)
    status: Literal["active", "inactive", "on_leave"]
