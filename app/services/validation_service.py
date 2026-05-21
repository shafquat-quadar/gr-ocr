from __future__ import annotations

import logging

from app.models.schemas import MatchResult, ParsedFields, ValidationMessage, ValidationResult

logger = logging.getLogger(__name__)


def _err(code: str, message: str, details: dict | None = None) -> ValidationMessage:
    return ValidationMessage(code=code, severity="error", message=message, details=details)


def _warn(code: str, message: str, details: dict | None = None) -> ValidationMessage:
    return ValidationMessage(code=code, severity="warning", message=message, details=details)


class ValidationService:

    def validate_gr_candidate(
        self,
        parsed: ParsedFields,
        match: MatchResult,
        storage_location_override: str | None = None,
    ) -> ValidationResult:
        messages: list[ValidationMessage] = []
        storage_location = storage_location_override or match.storage_location or ""

        # --- PO checks ---
        if not parsed.po_number:
            messages.append(_err("PO_MISSING", "No purchase order number could be extracted from the image."))

        if parsed.po_number and not match.purchase_order:
            messages.append(_err("PO_NOT_FOUND", f"Purchase order {parsed.po_number!r} was not found in SAP."))

        if match.ambiguous and match.purchase_order and not match.matched:
            messages.append(
                _err(
                    "PO_ITEM_AMBIGUOUS",
                    "Multiple open PO items found; cannot auto-select. Please specify purchase_order_item.",
                    {"candidate_count": len(match.candidate_items)},
                )
            )

        if match.matched and match.deleted:
            messages.append(_err("PO_ITEM_DELETED", f"PO item {match.purchase_order_item} has been deleted."))

        if match.matched and match.delivery_completed:
            messages.append(
                _err(
                    "PO_ITEM_DELIVERY_COMPLETED",
                    f"PO item {match.purchase_order_item} is marked as delivery completed.",
                )
            )

        # --- Quantity checks ---
        if parsed.quantity is None:
            messages.append(_err("QUANTITY_MISSING", "No quantity could be extracted from the image."))
        elif parsed.quantity <= 0:
            messages.append(
                _err("INVALID_QUANTITY", f"Quantity must be greater than 0 (got {parsed.quantity}).")
            )
        elif match.matched:
            if match.open_quantity is None:
                messages.append(
                    _err(
                        "OPEN_QTY_NOT_AVAILABLE_FROM_API",
                        "Open quantity could not be determined from SAP. Posting is blocked.",
                    )
                )
            elif parsed.quantity > match.open_quantity:
                messages.append(
                    _err(
                        "QUANTITY_EXCEEDS_OPEN_QTY",
                        f"Requested GR quantity {parsed.quantity} {parsed.entry_unit or ''} exceeds "
                        f"open PO quantity {match.open_quantity} {match.unit or ''}.",
                        {
                            "requested_quantity": parsed.quantity,
                            "open_quantity": match.open_quantity,
                            "unit": match.unit,
                        },
                    )
                )

        # --- Unit checks ---
        if not parsed.entry_unit:
            if match.unit:
                messages.append(
                    _warn(
                        "UNIT_MISSING",
                        f"No unit of measure found; will default to PO unit {match.unit!r}.",
                        {"defaulted_unit": match.unit},
                    )
                )
            else:
                messages.append(_err("UNIT_MISSING", "No unit of measure found and PO item has no unit."))
        elif match.unit and parsed.entry_unit.upper() != match.unit.upper():
            messages.append(
                _err(
                    "UNIT_MISMATCH",
                    f"OCR unit {parsed.entry_unit!r} does not match PO unit {match.unit!r}.",
                    {"ocr_unit": parsed.entry_unit, "po_unit": match.unit},
                )
            )

        # --- Batch checks ---
        if match.batch_required and not parsed.batch:
            messages.append(
                _err(
                    "BATCH_REQUIRED_MISSING",
                    f"PO item {match.purchase_order_item} requires a batch/lot number but none was extracted.",
                )
            )

        # --- Serial number checks ---
        if match.serial_required:
            if not parsed.serial_numbers:
                messages.append(
                    _err(
                        "SERIAL_REQUIRED_MISSING",
                        f"PO item {match.purchase_order_item} requires serial numbers but none were extracted.",
                    )
                )
            elif parsed.quantity is not None and len(parsed.serial_numbers) != int(parsed.quantity):
                messages.append(
                    _err(
                        "SERIAL_COUNT_MISMATCH",
                        f"Serial number count ({len(parsed.serial_numbers)}) does not match "
                        f"quantity ({int(parsed.quantity)}).",
                        {
                            "serial_count": len(parsed.serial_numbers),
                            "quantity": parsed.quantity,
                        },
                    )
                )

        # --- Storage location check ---
        if not storage_location:
            if match.storage_location:
                messages.append(
                    _warn(
                        "STORAGE_LOCATION_MISSING",
                        f"No storage location provided; will default to PO item storage location "
                        f"{match.storage_location!r}.",
                        {"defaulted_storage_location": match.storage_location},
                    )
                )
            else:
                messages.append(
                    _err(
                        "STORAGE_LOCATION_MISSING",
                        "No storage location found in OCR or PO item.",
                    )
                )

        errors = [m for m in messages if m.severity == "error"]
        can_post = len(errors) == 0 and match.matched

        if can_post:
            status = "VALID"
        elif errors:
            status = "INVALID"
        else:
            status = "WARNING"

        return ValidationResult(
            validation_status=status,
            can_post=can_post,
            messages=messages,
            matched_item=match if match.matched else None,
            candidate_items=match.candidate_items if match.ambiguous else [],
        )
