from fastapi import FastAPI

from app.exceptions import (
    DepartmentAlreadyExistError,
    DepartmentNotFoundError,
    EmployeeEmailAlreadyExistError,
    EmployeeNotFoundError,
    department_already_exist_handler,
    department_not_found_handler,
    employee_email_exist_handler,
    employee_not_found_handler,
)
from app.routers import router as e
from app.routers.auth import router as auth_router
from app.routers.deparments import router as d

app = FastAPI(
    title="Employee Management API",
    version="0.1.0",
)
app.add_exception_handler(
    EmployeeNotFoundError,
    employee_not_found_handler,
)
app.add_exception_handler(
    EmployeeEmailAlreadyExistError,
    employee_email_exist_handler,
)
app.add_exception_handler(
    DepartmentAlreadyExistError,
    department_already_exist_handler,
)
app.add_exception_handler(
    DepartmentNotFoundError,
    department_not_found_handler,
)

app.include_router(auth_router)
app.include_router(e)
app.include_router(d)
