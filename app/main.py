from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    del request

    messages = {
        400: "Bad request",
        401: "Authentication required or invalid credentials",
        403: "Permission denied",
        404: "Resource not found",
        405: "Method not allowed",
        409: "Conflict",
        422: "Request validation failed",
    }

    message = messages.get(exc.status_code, str(exc.detail))

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": message,
            "error_code": f"HTTP_{exc.status_code}",
            "details": exc.detail,
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    del request

    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "status_code": 422,
            "message": "Request validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": errors,
        },
    )

app.include_router(auth_router,prefix="/api/v3")
app.include_router(e,prefix="/api/v1")
app.include_router(d,prefix="/api/v2")
