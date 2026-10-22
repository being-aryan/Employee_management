
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    status_code: int
    message: str
    data: T


class APIErrorResponse(BaseModel):
    success: bool = False
    status_code: int
    message: str
    error_code: str
    details: list[dict[str, str]] | None = None


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"


class EmployeeBase(BaseModel):
    id: int = Field(ge=1)
    name: str = Field(min_length=2)
    email: EmailStr
    department: str = Field(min_length=2)
    salary: float = Field(ge=0)
    status: EmployeeStatus


class Employee(EmployeeBase):
    is_deleted: bool = False


class DeletedEmployee(EmployeeBase):
    is_deleted: bool = True


class EmployeeStatusUpdate(BaseModel):
    status: EmployeeStatus


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    email: EmailStr | None = None
    department: str | None = Field(default=None, min_length=2)
    salary: float | None = Field(default=None, ge=0)
    status: EmployeeStatus | None = None


class CreateEmployee(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    department: str = Field(min_length=2)
    salary: float = Field(ge=0)
    status: EmployeeStatus


class EmployeeReplace(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    department: str = Field(min_length=2)
    salary: float = Field(ge=0)
    status: EmployeeStatus


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationMeta
