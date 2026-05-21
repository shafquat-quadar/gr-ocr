from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GRRequest(Base):
    __tablename__ = "gr_request"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    source_channel: Mapped[str] = mapped_column(String, default="local")
    image_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    image_sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    idempotency_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="CREATED")
    sap_mode: Mapped[str] = mapped_column(String, default="mock")

    ocr_results: Mapped[list[OCRResult]] = relationship("OCRResult", back_populates="request")
    parsed_fields: Mapped[list[ParsedFields]] = relationship("ParsedFields", back_populates="request")
    sap_validations: Mapped[list[SAPValidation]] = relationship("SAPValidation", back_populates="request")
    sap_postings: Mapped[list[SAPPosting]] = relationship("SAPPosting", back_populates="request")


class OCRResult(Base):
    __tablename__ = "ocr_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("gr_request.request_id"), nullable=False)
    ocr_engine: Mapped[str] = mapped_column(String)
    raw_text: Mapped[str] = mapped_column(Text)
    ocr_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    request: Mapped[GRRequest] = relationship("GRRequest", back_populates="ocr_results")


class ParsedFields(Base):
    __tablename__ = "parsed_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("gr_request.request_id"), nullable=False)
    po_number: Mapped[str | None] = mapped_column(String, nullable=True)
    purchase_order_item: Mapped[str | None] = mapped_column(String, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_unit: Mapped[str | None] = mapped_column(String, nullable=True)
    batch: Mapped[str | None] = mapped_column(String, nullable=True)
    serial_numbers_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    material_text_hint: Mapped[str | None] = mapped_column(String, nullable=True)
    field_confidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_map_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now)

    request: Mapped[GRRequest] = relationship("GRRequest", back_populates="parsed_fields")


class SAPValidation(Base):
    __tablename__ = "sap_validation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("gr_request.request_id"), nullable=False)
    purchase_order: Mapped[str | None] = mapped_column(String, nullable=True)
    purchase_order_item: Mapped[str | None] = mapped_column(String, nullable=True)
    material: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    plant: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String, nullable=True)
    order_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    received_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    open_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    batch_required: Mapped[bool] = mapped_column(Boolean, default=False)
    serial_required: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_status: Mapped[str] = mapped_column(String)
    can_post: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_messages_json: Mapped[str] = mapped_column(Text)
    candidate_items_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    request: Mapped[GRRequest] = relationship("GRRequest", back_populates="sap_validations")


class SAPPosting(Base):
    __tablename__ = "sap_posting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("gr_request.request_id"), nullable=False)
    posting_payload_json: Mapped[str] = mapped_column(Text)
    posting_response_json: Mapped[str] = mapped_column(Text)
    posting_status: Mapped[str] = mapped_column(String)
    material_document: Mapped[str | None] = mapped_column(String, nullable=True)
    material_document_year: Mapped[str | None] = mapped_column(String, nullable=True)
    posted_by: Mapped[str | None] = mapped_column(String, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    request: Mapped[GRRequest] = relationship("GRRequest", back_populates="sap_postings")


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[str] = mapped_column(String)
    actor_type: Mapped[str] = mapped_column(String)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=_now)
