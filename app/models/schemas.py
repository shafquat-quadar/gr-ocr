from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    raw_text: str
    engine: str
    overall_confidence: float | None = None
    debug_metadata: dict[str, Any] | None = None


class ParsedFieldSource(BaseModel):
    field: str
    raw_value: str
    normalized_value: str | None = None
    rule_name: str
    normalized: bool = False


class ParsedFields(BaseModel):
    po_number: str | None = None
    purchase_order_item: str | None = None
    quantity: float | None = None
    entry_unit: str | None = None
    batch: str | None = None
    serial_numbers: list[str] = Field(default_factory=list)
    material_text_hint: str | None = None
    field_confidence: dict[str, float] = Field(default_factory=dict)
    source_map: list[ParsedFieldSource] = Field(default_factory=list)
    ambiguous_po: bool = False
    ambiguous_quantity: bool = False
    po_candidates: list[str] = Field(default_factory=list)
    quantity_candidates: list[float] = Field(default_factory=list)


class PurchaseOrderItem(BaseModel):
    purchase_order_item: str
    material: str
    description: str
    plant: str
    storage_location: str | None = None
    order_quantity: float
    received_quantity: float
    open_quantity: float | None = None
    unit: str
    batch_required: bool = False
    serial_required: bool = False
    deleted: bool = False
    delivery_completed: bool = False


class PurchaseOrder(BaseModel):
    purchase_order: str
    supplier: str | None = None
    company_code: str | None = None
    items: list[PurchaseOrderItem] = Field(default_factory=list)


class MatchResult(BaseModel):
    matched: bool = False
    purchase_order: str | None = None
    purchase_order_item: str | None = None
    material: str | None = None
    description: str | None = None
    plant: str | None = None
    storage_location: str | None = None
    order_quantity: float | None = None
    received_quantity: float | None = None
    open_quantity: float | None = None
    unit: str | None = None
    batch_required: bool = False
    serial_required: bool = False
    deleted: bool = False
    delivery_completed: bool = False
    match_method: str | None = None
    match_score: float | None = None
    ambiguous: bool = False
    candidate_items: list[PurchaseOrderItem] = Field(default_factory=list)


class ValidationMessage(BaseModel):
    code: str
    severity: str  # "error" | "warning" | "info"
    message: str
    details: dict[str, Any] | None = None


class ValidationResult(BaseModel):
    validation_status: str  # "VALID" | "INVALID" | "WARNING"
    can_post: bool = False
    messages: list[ValidationMessage] = Field(default_factory=list)
    matched_item: MatchResult | None = None
    candidate_items: list[PurchaseOrderItem] = Field(default_factory=list)


class GRDraftParsedView(BaseModel):
    po_number: str | None = None
    purchase_order_item: str | None = None
    quantity: float | None = None
    entry_unit: str | None = None
    batch: str | None = None
    serial_numbers: list[str] = Field(default_factory=list)
    material_text_hint: str | None = None


class GRMatchedPOItemView(BaseModel):
    purchase_order: str | None = None
    purchase_order_item: str | None = None
    material: str | None = None
    description: str | None = None
    plant: str | None = None
    storage_location: str | None = None
    open_quantity: float | None = None
    unit: str | None = None


class GRDraftResponse(BaseModel):
    request_id: str
    status: str
    sap_mode: str
    ocr_text: str | None = None
    parsed: GRDraftParsedView | None = None
    matched_po_item: GRMatchedPOItemView | None = None
    validation_messages: list[ValidationMessage] = Field(default_factory=list)
    candidate_items: list[PurchaseOrderItem] = Field(default_factory=list)
    requires_human_confirmation: bool = True
    can_post: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GRDraftPatchRequest(BaseModel):
    po_number: str | None = None
    purchase_order_item: str | None = None
    quantity: float | None = None
    entry_unit: str | None = None
    batch: str | None = None
    serial_numbers: list[str] | None = None
    storage_location: str | None = None


class GRConfirmRequest(BaseModel):
    confirmed_by: str
    posting_date: date | None = None
    document_date: date | None = None


class GRConfirmResponse(BaseModel):
    request_id: str
    status: str
    material_document: str | None = None
    material_document_year: str | None = None
    message: str


class GRRejectRequest(BaseModel):
    rejected_by: str
    reason: str


class AuditEventResponse(BaseModel):
    id: int
    request_id: str
    event_type: str
    actor_type: str
    actor_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SAPPostResult(BaseModel):
    material_document: str | None = None
    material_document_year: str | None = None
    status: str
    message: str


class SAPErrorResponse(BaseModel):
    error: dict[str, Any]
