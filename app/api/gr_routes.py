from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.main_deps import get_orchestrator
from app.models.schemas import (
    AuditEventResponse,
    GRConfirmRequest,
    GRConfirmResponse,
    GRDraftPatchRequest,
    GRDraftResponse,
    GRRejectRequest,
)
from app.services.gr_orchestrator import GROrchestrator

router = APIRouter(prefix="/api/v1/gr", tags=["goods-receipt"])


@router.post("/drafts", response_model=GRDraftResponse, status_code=202)
def create_draft(
    file: Annotated[UploadFile, File(description="Package/label image (JPEG or PNG)")],
    created_by: Annotated[str | None, Form()] = None,
    plant_hint: Annotated[str | None, Form()] = None,
    storage_location_hint: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    orchestrator: GROrchestrator = Depends(get_orchestrator),
) -> GRDraftResponse:
    return orchestrator.create_draft_from_image(
        db=db,
        file=file,
        created_by=created_by,
        plant_hint=plant_hint,
        storage_location_hint=storage_location_hint,
    )


@router.get("/drafts/{request_id}", response_model=GRDraftResponse)
def get_draft(
    request_id: str,
    db: Session = Depends(get_db),
    orchestrator: GROrchestrator = Depends(get_orchestrator),
) -> GRDraftResponse:
    return orchestrator.get_draft(db=db, request_id=request_id)


@router.patch("/drafts/{request_id}", response_model=GRDraftResponse)
def patch_draft(
    request_id: str,
    patch: GRDraftPatchRequest,
    db: Session = Depends(get_db),
    orchestrator: GROrchestrator = Depends(get_orchestrator),
) -> GRDraftResponse:
    return orchestrator.patch_draft(db=db, request_id=request_id, patch=patch.model_dump(exclude_unset=True))


@router.post("/drafts/{request_id}/validate", response_model=GRDraftResponse)
def validate_draft(
    request_id: str,
    db: Session = Depends(get_db),
    orchestrator: GROrchestrator = Depends(get_orchestrator),
) -> GRDraftResponse:
    return orchestrator.validate_draft(db=db, request_id=request_id)


@router.post("/drafts/{request_id}/confirm", response_model=GRConfirmResponse)
def confirm_draft(
    request_id: str,
    body: GRConfirmRequest,
    db: Session = Depends(get_db),
    orchestrator: GROrchestrator = Depends(get_orchestrator),
) -> GRConfirmResponse:
    return orchestrator.confirm_and_post(
        db=db,
        request_id=request_id,
        confirmed_by=body.confirmed_by,
        posting_date=body.posting_date,
        document_date=body.document_date,
    )


@router.post("/drafts/{request_id}/reject", response_model=GRDraftResponse)
def reject_draft(
    request_id: str,
    body: GRRejectRequest,
    db: Session = Depends(get_db),
    orchestrator: GROrchestrator = Depends(get_orchestrator),
) -> GRDraftResponse:
    return orchestrator.reject_draft(
        db=db,
        request_id=request_id,
        rejected_by=body.rejected_by,
        reason=body.reason,
    )


@router.get("/drafts/{request_id}/audit", response_model=list[AuditEventResponse])
def get_audit(
    request_id: str,
    db: Session = Depends(get_db),
    orchestrator: GROrchestrator = Depends(get_orchestrator),
) -> list[AuditEventResponse]:
    from app.services.audit_service import AuditService
    audit_svc = AuditService()
    return audit_svc.get_events(db=db, request_id=request_id)
