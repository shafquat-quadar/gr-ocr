from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timezone
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.db_models import (
    GRRequest,
    OCRResult as DBOCRResult,
    ParsedFields as DBParsedFields,
    SAPPosting,
    SAPValidation,
)
from app.models.schemas import (
    GRConfirmResponse,
    GRDraftParsedView,
    GRDraftResponse,
    GRMatchedPOItemView,
    MatchResult,
    ParsedFields,
    PurchaseOrder,
    PurchaseOrderItem,
    ValidationResult,
)
from app.sap.sap_adapter import SAPAdapter
from app.services.audit_service import AuditService
from app.services.image_service import ImageService
from app.services.matching_service import MatchingService
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)

_POSTABLE_STATUSES = {"VALIDATED", "READY_FOR_CONFIRMATION"}


class GROrchestrator:

    def __init__(
        self,
        sap_adapter: SAPAdapter,
        sap_mode: str,
        image_service: ImageService,
        ocr_service: OCRService,
        parser_service: ParserService,
        matching_service: MatchingService,
        validation_service: ValidationService,
        audit_service: AuditService,
    ):
        self._sap = sap_adapter
        self._sap_mode = sap_mode
        self._img = image_service
        self._ocr = ocr_service
        self._parser = parser_service
        self._matcher = matching_service
        self._validator = validation_service
        self._audit = audit_service

    # ------------------------------------------------------------------ #
    #  CREATE DRAFT                                                        #
    # ------------------------------------------------------------------ #

    def create_draft_from_image(
        self,
        db: Session,
        file: UploadFile,
        created_by: str | None = None,
        plant_hint: str | None = None,
        storage_location_hint: str | None = None,
    ) -> GRDraftResponse:

        # 1. Save image
        img_meta = self._img.validate_and_save(file)
        request_id = img_meta["request_id"]

        # 2. Create DB record
        gr = GRRequest(
            request_id=request_id,
            created_by=created_by,
            image_uri=img_meta["image_uri"],
            image_sha256=img_meta["image_sha256"],
            status="IMAGE_UPLOADED",
            sap_mode=self._sap_mode,
        )
        db.add(gr)
        db.flush()
        self._audit.create_event(db, request_id, "IMAGE_UPLOADED", actor_id=created_by,
                                  payload={"image_uri": img_meta["image_uri"],
                                           "sha256": img_meta["image_sha256"]})

        # 3. OCR
        try:
            ocr_result = self._ocr.extract_text(img_meta["image_uri"])
        except Exception as exc:
            gr.status = "FAILED"
            db.commit()
            raise HTTPException(500, detail={"error": {"code": "OCR_FAILED", "message": str(exc)}}) from exc

        db_ocr = DBOCRResult(
            request_id=request_id,
            ocr_engine=ocr_result.engine,
            raw_text=ocr_result.raw_text,
            ocr_json=json.dumps(ocr_result.debug_metadata or {}, default=str),
            overall_confidence=ocr_result.overall_confidence,
        )
        db.add(db_ocr)
        gr.status = "OCR_COMPLETED"
        self._audit.create_event(db, request_id, "OCR_COMPLETED",
                                  payload={"text_length": len(ocr_result.raw_text)})

        # 4. Parse
        parsed = self._parser.parse(ocr_result.raw_text)
        db_parsed = DBParsedFields(
            request_id=request_id,
            po_number=parsed.po_number,
            purchase_order_item=parsed.purchase_order_item,
            quantity=parsed.quantity,
            entry_unit=parsed.entry_unit,
            batch=parsed.batch,
            serial_numbers_json=json.dumps(parsed.serial_numbers),
            material_text_hint=parsed.material_text_hint,
            field_confidence_json=json.dumps(parsed.field_confidence),
            source_map_json=json.dumps([s.model_dump() for s in parsed.source_map]),
        )
        db.add(db_parsed)
        gr.status = "PARSING_COMPLETED"
        self._audit.create_event(db, request_id, "FIELDS_PARSED",
                                  payload={"po_number": parsed.po_number,
                                           "quantity": parsed.quantity,
                                           "batch": parsed.batch,
                                           "ambiguous_po": parsed.ambiguous_po,
                                           "ambiguous_quantity": parsed.ambiguous_quantity})

        # 5. Validate against SAP
        match, validation = self._run_validation(db, request_id, parsed, storage_location_hint)

        # 6. Set final status
        gr.status = self._derive_status(parsed, validation)
        db.commit()

        return self._build_response(gr, ocr_result.raw_text, parsed, match, validation)

    # ------------------------------------------------------------------ #
    #  PATCH DRAFT                                                        #
    # ------------------------------------------------------------------ #

    def patch_draft(
        self,
        db: Session,
        request_id: str,
        patch: dict[str, Any],
    ) -> GRDraftResponse:
        gr = self._load_request(db, request_id)
        self._assert_not_terminal(gr)

        db_parsed = db.query(DBParsedFields).filter(
            DBParsedFields.request_id == request_id
        ).order_by(DBParsedFields.id.desc()).first()
        if not db_parsed:
            raise HTTPException(404, detail={"error": {"code": "DRAFT_NOT_FOUND", "message": "Parsed fields missing."}})

        updated_fields: dict[str, Any] = {}
        if "po_number" in patch and patch["po_number"] is not None:
            db_parsed.po_number = patch["po_number"]
            updated_fields["po_number"] = patch["po_number"]
        if "purchase_order_item" in patch and patch["purchase_order_item"] is not None:
            db_parsed.purchase_order_item = patch["purchase_order_item"]
            updated_fields["purchase_order_item"] = patch["purchase_order_item"]
        if "quantity" in patch and patch["quantity"] is not None:
            db_parsed.quantity = patch["quantity"]
            updated_fields["quantity"] = patch["quantity"]
        if "entry_unit" in patch and patch["entry_unit"] is not None:
            db_parsed.entry_unit = patch["entry_unit"]
            updated_fields["entry_unit"] = patch["entry_unit"]
        if "batch" in patch and patch["batch"] is not None:
            db_parsed.batch = patch["batch"]
            updated_fields["batch"] = patch["batch"]
        if "serial_numbers" in patch and patch["serial_numbers"] is not None:
            db_parsed.serial_numbers_json = json.dumps(patch["serial_numbers"])
            updated_fields["serial_numbers"] = patch["serial_numbers"]

        storage_location_override = patch.get("storage_location")

        self._audit.create_event(db, request_id, "USER_CORRECTED_DRAFT", actor_type="human",
                                  payload={"updated_fields": updated_fields})
        db.flush()

        parsed = self._db_parsed_to_schema(db_parsed)
        match, validation = self._run_validation(db, request_id, parsed, storage_location_override)
        self._audit.create_event(db, request_id, "DRAFT_REVALIDATED",
                                  payload={"can_post": validation.can_post})

        gr.status = self._derive_status(parsed, validation)
        db.commit()

        db_ocr = db.query(DBOCRResult).filter(
            DBOCRResult.request_id == request_id
        ).order_by(DBOCRResult.id.desc()).first()
        ocr_text = db_ocr.raw_text if db_ocr else ""
        return self._build_response(gr, ocr_text, parsed, match, validation)

    # ------------------------------------------------------------------ #
    #  REVALIDATE                                                         #
    # ------------------------------------------------------------------ #

    def validate_draft(self, db: Session, request_id: str) -> GRDraftResponse:
        gr = self._load_request(db, request_id)
        self._assert_not_terminal(gr)

        db_parsed = db.query(DBParsedFields).filter(
            DBParsedFields.request_id == request_id
        ).order_by(DBParsedFields.id.desc()).first()
        if not db_parsed:
            raise HTTPException(404, detail={"error": {"code": "DRAFT_NOT_FOUND", "message": "Parsed fields missing."}})

        parsed = self._db_parsed_to_schema(db_parsed)
        match, validation = self._run_validation(db, request_id, parsed, None)
        self._audit.create_event(db, request_id, "DRAFT_REVALIDATED",
                                  payload={"can_post": validation.can_post,
                                           "status": validation.validation_status})
        gr.status = self._derive_status(parsed, validation)
        db.commit()

        db_ocr = db.query(DBOCRResult).filter(
            DBOCRResult.request_id == request_id
        ).order_by(DBOCRResult.id.desc()).first()
        ocr_text = db_ocr.raw_text if db_ocr else ""
        return self._build_response(gr, ocr_text, parsed, match, validation)

    # ------------------------------------------------------------------ #
    #  CONFIRM AND POST                                                   #
    # ------------------------------------------------------------------ #

    def confirm_and_post(
        self,
        db: Session,
        request_id: str,
        confirmed_by: str,
        posting_date: date | None = None,
        document_date: date | None = None,
    ) -> GRConfirmResponse:
        gr = self._load_request(db, request_id)

        if gr.status not in _POSTABLE_STATUSES:
            raise HTTPException(
                409,
                detail={
                    "error": {
                        "code": "INVALID_STATUS_FOR_POSTING",
                        "message": f"Cannot post in status {gr.status!r}. Required: {_POSTABLE_STATUSES}",
                    }
                },
            )

        # Check already posted
        existing_posting = db.query(SAPPosting).filter(
            SAPPosting.request_id == request_id,
            SAPPosting.posting_status == "POSTED",
        ).first()
        if existing_posting:
            raise HTTPException(
                409,
                detail={
                    "error": {
                        "code": "ALREADY_POSTED",
                        "message": f"Request {request_id} has already been posted as material document "
                                   f"{existing_posting.material_document}.",
                    }
                },
            )

        db_parsed = db.query(DBParsedFields).filter(
            DBParsedFields.request_id == request_id
        ).order_by(DBParsedFields.id.desc()).first()
        if not db_parsed:
            raise HTTPException(404, detail={"error": {"code": "DRAFT_NOT_FOUND", "message": "Parsed fields missing."}})

        parsed = self._db_parsed_to_schema(db_parsed)

        # Final revalidation before posting
        match, validation = self._run_validation(db, request_id, parsed, None)
        if not validation.can_post:
            gr.status = "BLOCKED"
            db.commit()
            raise HTTPException(
                422,
                detail={
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "Draft failed revalidation before posting.",
                        "details": [m.model_dump() for m in validation.messages if m.severity == "error"],
                    }
                },
            )

        # Build idempotency hash
        serial_str = ",".join(sorted(parsed.serial_numbers))
        raw_hash = (
            f"{parsed.po_number}|{match.purchase_order_item}|{parsed.quantity}|"
            f"{parsed.entry_unit}|{parsed.batch or ''}|{serial_str}|{gr.image_sha256}"
        )
        idem_hash = hashlib.sha256(raw_hash.encode()).hexdigest()

        # Check duplicate
        dup = db.query(GRRequest).filter(
            GRRequest.idempotency_hash == idem_hash,
            GRRequest.status == "POSTED",
        ).first()
        if dup:
            self._audit.create_event(
                db, request_id, "DUPLICATE_POSTING_BLOCKED", actor_type="system",
                payload={"duplicate_of": dup.request_id, "idempotency_hash": idem_hash}
            )
            db.commit()
            raise HTTPException(
                409,
                detail={
                    "error": {
                        "code": "DUPLICATE_POSTING",
                        "message": f"Identical goods receipt already posted as {dup.request_id}.",
                        "details": {"duplicate_request_id": dup.request_id},
                    }
                },
            )

        gr.idempotency_hash = idem_hash

        today = date.today()
        posting_date = posting_date or today
        document_date = document_date or today

        canonical_payload = {
            "movement_type": "101",
            "goods_movement_code": "01",
            "purchase_order": parsed.po_number,
            "purchase_order_item": match.purchase_order_item,
            "material": match.material,
            "plant": match.plant,
            "storage_location": match.storage_location or "",
            "quantity": parsed.quantity,
            "entry_unit": parsed.entry_unit or match.unit,
            "batch": parsed.batch or "",
            "serial_numbers": parsed.serial_numbers,
            "posting_date": posting_date.isoformat(),
            "document_date": document_date.isoformat(),
            "header_text": f"GR via OCR agent {request_id}",
        }

        self._audit.create_event(
            db, request_id, "POSTING_REQUESTED", actor_type="human", actor_id=confirmed_by,
            payload={"confirmed_by": confirmed_by, "posting_date": str(posting_date)}
        )

        gr.status = "POSTING_IN_PROGRESS"
        db.flush()

        try:
            post_result = self._sap.post_goods_receipt(canonical_payload)
        except Exception as exc:
            logger.error("SAP posting failed for %s: %s", request_id, exc)
            gr.status = "FAILED"
            posting = SAPPosting(
                request_id=request_id,
                posting_payload_json=json.dumps(canonical_payload, default=str),
                posting_response_json=json.dumps({"error": str(exc)}),
                posting_status="FAILED",
                posted_by=confirmed_by,
                posted_at=datetime.now(timezone.utc),
            )
            db.add(posting)
            self._audit.create_event(db, request_id, "GR_POSTING_FAILED",
                                      payload={"error": str(exc)})
            db.commit()
            raise HTTPException(
                502,
                detail={
                    "error": {
                        "code": "SAP_POSTING_FAILED",
                        "message": str(exc),
                    }
                },
            ) from exc

        posting = SAPPosting(
            request_id=request_id,
            posting_payload_json=json.dumps(canonical_payload, default=str),
            posting_response_json=json.dumps(post_result, default=str),
            posting_status="POSTED",
            material_document=post_result.get("material_document"),
            material_document_year=post_result.get("material_document_year"),
            posted_by=confirmed_by,
            posted_at=datetime.now(timezone.utc),
        )
        db.add(posting)
        gr.status = "POSTED"
        self._audit.create_event(
            db, request_id, "GR_POSTED", actor_type="human", actor_id=confirmed_by,
            payload={
                "material_document": post_result.get("material_document"),
                "material_document_year": post_result.get("material_document_year"),
            },
        )
        db.commit()

        return GRConfirmResponse(
            request_id=request_id,
            status="POSTED",
            material_document=post_result.get("material_document"),
            material_document_year=post_result.get("material_document_year"),
            message=post_result.get("message", "Posted successfully"),
        )

    # ------------------------------------------------------------------ #
    #  REJECT                                                             #
    # ------------------------------------------------------------------ #

    def reject_draft(
        self,
        db: Session,
        request_id: str,
        rejected_by: str,
        reason: str,
    ) -> GRDraftResponse:
        gr = self._load_request(db, request_id)
        self._assert_not_terminal(gr)
        gr.status = "REJECTED"
        self._audit.create_event(
            db, request_id, "DRAFT_REJECTED", actor_type="human", actor_id=rejected_by,
            payload={"rejected_by": rejected_by, "reason": reason}
        )
        db.commit()
        return self.get_draft(db, request_id)

    # ------------------------------------------------------------------ #
    #  GET DRAFT                                                          #
    # ------------------------------------------------------------------ #

    def get_draft(self, db: Session, request_id: str) -> GRDraftResponse:
        gr = self._load_request(db, request_id)
        db_ocr = db.query(DBOCRResult).filter(
            DBOCRResult.request_id == request_id
        ).order_by(DBOCRResult.id.desc()).first()
        db_parsed = db.query(DBParsedFields).filter(
            DBParsedFields.request_id == request_id
        ).order_by(DBParsedFields.id.desc()).first()
        db_val = db.query(SAPValidation).filter(
            SAPValidation.request_id == request_id
        ).order_by(SAPValidation.id.desc()).first()

        parsed = self._db_parsed_to_schema(db_parsed) if db_parsed else None
        match = self._db_val_to_match(db_val) if db_val else MatchResult()
        validation = self._db_val_to_validation(db_val) if db_val else ValidationResult(
            validation_status="UNKNOWN", can_post=False
        )

        return self._build_response(
            gr, db_ocr.raw_text if db_ocr else "", parsed, match, validation
        )

    # ------------------------------------------------------------------ #
    #  INTERNAL HELPERS                                                   #
    # ------------------------------------------------------------------ #

    def _run_validation(
        self,
        db: Session,
        request_id: str,
        parsed: ParsedFields,
        storage_location_hint: str | None,
    ) -> tuple[MatchResult, ValidationResult]:
        match = MatchResult()
        validation = ValidationResult(validation_status="INVALID", can_post=False)

        if parsed.po_number and not parsed.ambiguous_po:
            try:
                raw_po = self._sap.get_purchase_order(parsed.po_number)
                po = PurchaseOrder(**raw_po)
                self._audit.create_event(db, request_id, "SAP_PO_READ",
                                          payload={"po_number": parsed.po_number,
                                                   "item_count": len(po.items)})
                match = self._matcher.match_po_item(parsed, po)
            except KeyError:
                pass
            except Exception as exc:
                logger.warning("SAP PO read failed for %s: %s", parsed.po_number, exc)

        validation = self._validator.validate_gr_candidate(parsed, match, storage_location_hint)
        self._audit.create_event(db, request_id, "SAP_VALIDATION_COMPLETED",
                                  payload={"can_post": validation.can_post,
                                           "status": validation.validation_status,
                                           "error_count": len([m for m in validation.messages
                                                                if m.severity == "error"])})

        # Store validation in DB
        db_val = SAPValidation(
            request_id=request_id,
            purchase_order=match.purchase_order or parsed.po_number,
            purchase_order_item=match.purchase_order_item,
            material=match.material,
            description=match.description,
            plant=match.plant,
            storage_location=match.storage_location,
            order_quantity=match.order_quantity,
            received_quantity=match.received_quantity,
            open_quantity=match.open_quantity,
            unit=match.unit,
            batch_required=match.batch_required,
            serial_required=match.serial_required,
            validation_status=validation.validation_status,
            can_post=validation.can_post,
            validation_messages_json=json.dumps([m.model_dump() for m in validation.messages]),
            candidate_items_json=json.dumps(
                [it.model_dump() for it in validation.candidate_items]
            ) if validation.candidate_items else None,
        )
        db.add(db_val)
        db.flush()
        return match, validation

    def _derive_status(self, parsed: ParsedFields, validation: ValidationResult) -> str:
        if validation.can_post:
            return "READY_FOR_CONFIRMATION"
        errors = [m for m in validation.messages if m.severity == "error"]
        if not errors:
            return "VALIDATED"
        # Critical blocking errors
        blocking_codes = {"PO_NOT_FOUND", "PO_ITEM_DELETED", "PO_ITEM_DELIVERY_COMPLETED",
                          "OPEN_QTY_NOT_AVAILABLE_FROM_API", "QUANTITY_EXCEEDS_OPEN_QTY"}
        if any(m.code in blocking_codes for m in errors):
            return "BLOCKED"
        return "NEEDS_CORRECTION"

    def _load_request(self, db: Session, request_id: str) -> GRRequest:
        gr = db.query(GRRequest).filter(GRRequest.request_id == request_id).first()
        if not gr:
            raise HTTPException(
                404,
                detail={"error": {"code": "REQUEST_NOT_FOUND",
                                   "message": f"Request {request_id!r} not found."}},
            )
        return gr

    def _assert_not_terminal(self, gr: GRRequest) -> None:
        terminal = {"POSTED", "REJECTED"}
        if gr.status in terminal:
            raise HTTPException(
                409,
                detail={
                    "error": {
                        "code": "TERMINAL_STATUS",
                        "message": f"Request {gr.request_id} is in terminal status {gr.status!r}.",
                    }
                },
            )

    def _db_parsed_to_schema(self, db_parsed: DBParsedFields) -> ParsedFields:
        return ParsedFields(
            po_number=db_parsed.po_number,
            purchase_order_item=db_parsed.purchase_order_item,
            quantity=db_parsed.quantity,
            entry_unit=db_parsed.entry_unit,
            batch=db_parsed.batch,
            serial_numbers=json.loads(db_parsed.serial_numbers_json or "[]"),
            material_text_hint=db_parsed.material_text_hint,
            field_confidence=json.loads(db_parsed.field_confidence_json or "{}"),
            source_map=[],
        )

    def _db_val_to_match(self, db_val: SAPValidation) -> MatchResult:
        return MatchResult(
            matched=bool(db_val.purchase_order_item and db_val.can_post is not None),
            purchase_order=db_val.purchase_order,
            purchase_order_item=db_val.purchase_order_item,
            material=db_val.material,
            description=db_val.description,
            plant=db_val.plant,
            storage_location=db_val.storage_location,
            order_quantity=db_val.order_quantity,
            received_quantity=db_val.received_quantity,
            open_quantity=db_val.open_quantity,
            unit=db_val.unit,
            batch_required=db_val.batch_required,
            serial_required=db_val.serial_required,
            candidate_items=self._parse_candidates(db_val.candidate_items_json),
        )

    def _db_val_to_validation(self, db_val: SAPValidation) -> ValidationResult:
        from app.models.schemas import ValidationMessage
        try:
            messages = [ValidationMessage(**m) for m in json.loads(db_val.validation_messages_json or "[]")]
        except Exception:
            messages = []
        return ValidationResult(
            validation_status=db_val.validation_status,
            can_post=db_val.can_post,
            messages=messages,
            candidate_items=self._parse_candidates(db_val.candidate_items_json),
        )

    def _parse_candidates(self, json_str: str | None) -> list[PurchaseOrderItem]:
        if not json_str:
            return []
        try:
            raw = json.loads(json_str)
            return [PurchaseOrderItem(**it) for it in raw]
        except Exception:
            return []

    def _build_response(
        self,
        gr: GRRequest,
        ocr_text: str,
        parsed: ParsedFields | None,
        match: MatchResult,
        validation: ValidationResult,
    ) -> GRDraftResponse:
        parsed_view = None
        if parsed:
            parsed_view = GRDraftParsedView(
                po_number=parsed.po_number,
                purchase_order_item=parsed.purchase_order_item,
                quantity=parsed.quantity,
                entry_unit=parsed.entry_unit,
                batch=parsed.batch,
                serial_numbers=parsed.serial_numbers,
                material_text_hint=parsed.material_text_hint,
            )

        matched_view = None
        if match.matched:
            matched_view = GRMatchedPOItemView(
                purchase_order=match.purchase_order,
                purchase_order_item=match.purchase_order_item,
                material=match.material,
                description=match.description,
                plant=match.plant,
                storage_location=match.storage_location,
                open_quantity=match.open_quantity,
                unit=match.unit,
            )

        return GRDraftResponse(
            request_id=gr.request_id,
            status=gr.status,
            sap_mode=gr.sap_mode,
            ocr_text=ocr_text,
            parsed=parsed_view,
            matched_po_item=matched_view,
            validation_messages=validation.messages,
            candidate_items=validation.candidate_items,
            requires_human_confirmation=True,
            can_post=validation.can_post,
            created_at=gr.created_at,
            updated_at=gr.updated_at,
        )
