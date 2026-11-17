from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import engine
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
from app.middleware.auth import add_auth_middleware
from app.middleware.cors import add_cors_middleware
from app.redis_client import redis_client
from app.routers import router as employee_router
from app.routers.auth import router as auth_router
from app.routers.departments import router as department_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    del app

    print("Starting Employee Management API...")

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        print("PostgreSQL connection established successfully.")

        await redis_client.ping()

        print("Redis connection established successfully.")

        yield

    finally:
        await redis_client.aclose()
        print("Redis connection closed.")

        await engine.dispose()
        print("PostgreSQL connection pool disposed.")


app = FastAPI(
    title="Employee Management API",
    version="0.1.0",
    lifespan=lifespan,
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


add_cors_middleware(app)
add_auth_middleware(app)


app.include_router(auth_router, prefix="/api/v3")
app.include_router(employee_router, prefix="/api/v1")
app.include_router(department_router, prefix="/api/v2")


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault(
        "securitySchemes",
        {},
    )

    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT access token.",
    }

    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if method.lower() not in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
                "trace",
            }:
                continue

            if path == "/api/v3/auth/login":
                operation["security"] = []
            else:
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi
