from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.sap.sap_adapter import SAPAdapter
from app.services.audit_service import AuditService
from app.services.gr_orchestrator import GROrchestrator
from app.services.image_service import ImageService
from app.services.matching_service import MatchingService
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.validation_service import ValidationService

settings = get_settings()


@lru_cache()
def get_sap_adapter() -> SAPAdapter:
    if settings.SAP_MODE == "real":
        from app.sap.real_sap_odata_adapter import RealSAPODataAdapter
        from app.sap.sap_client import SAPODataClient
        client = SAPODataClient(
            base_url=settings.SAP_BASE_URL,
            auth_type=settings.SAP_AUTH_TYPE,
            user=settings.SAP_USER or None,
            password=settings.SAP_PASSWORD or None,
            bearer_token=settings.SAP_BEARER_TOKEN or None,
            sap_client=settings.SAP_CLIENT or None,
            verify_ssl=settings.SAP_VERIFY_SSL,
            timeout_seconds=settings.SAP_TIMEOUT_SECONDS,
        )
        return RealSAPODataAdapter(client=client, sap_client_code=settings.SAP_CLIENT)
    else:
        from app.sap.mock_sap_adapter import MockSAPAdapter
        return MockSAPAdapter()


@lru_cache()
def get_orchestrator() -> GROrchestrator:
    return GROrchestrator(
        sap_adapter=get_sap_adapter(),
        sap_mode=settings.SAP_MODE,
        image_service=ImageService(),
        ocr_service=OCRService(),
        parser_service=ParserService(),
        matching_service=MatchingService(),
        validation_service=ValidationService(),
        audit_service=AuditService(),
    )
