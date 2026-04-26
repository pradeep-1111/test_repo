import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.webhook_routes import router as webhook_router
from app.core.config import get_settings
from app.workers.review_worker import get_review_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="MergeGuard", version="0.2.0")
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(webhook_router)

    @app.on_event("startup")
    def startup_event() -> None:
        get_review_worker().start()

    @app.on_event("shutdown")
    def shutdown_event() -> None:
        get_review_worker().stop()

    return app


app = create_app()