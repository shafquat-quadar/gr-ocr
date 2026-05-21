from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", tags=["health"])
def health_check() -> dict:
    return {
        "status": "ok",
        "sap_mode": settings.SAP_MODE,
        "ocr_engine": settings.OCR_ENGINE,
    }
