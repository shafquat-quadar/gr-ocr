from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.main_deps import get_sap_adapter

router = APIRouter(prefix="/api/v1/sap", tags=["sap"])
settings = get_settings()


@router.get("/ping")
def sap_ping(adapter=Depends(get_sap_adapter)) -> dict:
    result = adapter.ping()
    if settings.SAP_MODE == "mock":
        return {"sap_mode": "mock", "status": "ok"}
    return {
        "sap_mode": "real",
        "status": result.get("status", "unknown"),
        "base_url": settings.SAP_BASE_URL,
        "auth_type": settings.SAP_AUTH_TYPE,
        "material_document_service_reachable": result.get("material_document_service_reachable", False),
    }
