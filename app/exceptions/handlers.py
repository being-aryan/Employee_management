from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.employee import (
    DepartmentAlreadyExistError,
    DepartmentNotFoundError,
    EmployeeEmailAlreadyExistError,
    EmployeeNotFoundError,
)


async def employee_not_found_handler(
    request: Request,
    exc: EmployeeNotFoundError,
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "status_code": 404,
            "message": str(exc),
            "error_code": "EMPLOYEE_NOT_FOUND",
            "details": None,
        },
    )


async def employee_email_exist_handler(
    request: Request,
    exc: EmployeeEmailAlreadyExistError,
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "status_code": 409,
            "message": str(exc),
            "error_code": "EMPLOYEE_EMAIL_ALREADY_EXISTS",
            "details": None,
        },
    )


async def department_already_exist_handler(
    request: Request,
    exc: DepartmentAlreadyExistError,
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "status_code": 409,
            "message": str(exc),
            "error_code": "DEPARTMENT_ALREADY_EXISTS",
            "details": None,
        },
    )


async def department_not_found_handler(
    request: Request,
    exc: DepartmentNotFoundError,
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "status_code": 404,
            "message": str(exc),
            "error_code": "DEPARTMENT_NOT_FOUND",
            "details": None,
        },
    )
