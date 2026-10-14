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
        content={"detail": str(exc)},
    )


async def employee_email_exist_handler(
    request: Request,
    exc: EmployeeEmailAlreadyExistError,
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


async def department_already_exist_handler(
    request: Request,
    exc: DepartmentAlreadyExistError,
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


async def department_not_found_handler(
    request: Request,
    exc: DepartmentNotFoundError,
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )
