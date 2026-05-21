from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "OCR-Based SAP Goods Receipt Agent — local POC. "
            "Upload a package/label image to start a GR workflow."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.on_event("startup")
    def on_startup() -> None:
        logger.info("Starting %s in %s mode (SAP_MODE=%s)", settings.APP_NAME, settings.APP_ENV, settings.SAP_MODE)
        init_db()

    from app.api.health_routes import router as health_router
    from app.api.gr_routes import router as gr_router
    from app.api.sap_routes import router as sap_router

    app.include_router(health_router)
    app.include_router(gr_router)
    app.include_router(sap_router)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
        )

    return app


app = create_app()
