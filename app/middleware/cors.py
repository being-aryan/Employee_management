from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def add_cors_middleware(app: FastAPI) -> None:
    allowed_origins = [
        origin.strip()
        for origin in settings.cors_allowed_origins.split(",")
        if origin.strip()
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
