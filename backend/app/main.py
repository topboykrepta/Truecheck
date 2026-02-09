from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.config import settings
from app.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="TrueCheck API", version="0.1.0")

    origins = [o.strip() for o in settings.truecheck_cors_origins.split(",") if o.strip()]
    if settings.truecheck_env.lower() == "dev":
        # Common dev origins (including file:// which often sends Origin: null)
        for o in ("http://localhost:5173", "http://127.0.0.1:5173", "null"):
            if o not in origins:
                origins.append(o)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()
