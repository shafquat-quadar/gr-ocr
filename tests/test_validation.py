from __future__ import annotations

import pytest

from app.models.schemas import MatchResult, ParsedFields
from app.services.validation_service import ValidationService

validator = ValidationService()


def _match(**kwargs) -> MatchResult:
    defaults = dict(
        matched=True,
        purchase_order="4500166595",
        purchase_order_item="00010",
        material="MAT-100001",
        description="PRESSURE SENSOR ASSEMBLY",
        plant="1010",
        storage_location="0001",
        order_quantity=100,
        received_quantity=60,
        open_quantity=40,
        unit="EA",
        batch_required=False,
        serial_required=False,
        deleted=False,
        delivery_completed=False,
    )
    defaults.update(kwargs)
    return MatchResult(**defaults)


def _parsed(**kwargs) -> ParsedFields:
    defaults = dict(
        po_number="4500166595",
        quantity=10.0,
        entry_unit="EA",
    )
    defaults.update(kwargs)
    return ParsedFields(**defaults)


def _codes(result) -> list[str]:
    return [m.code for m in result.messages]


def test_valid_draft_can_post():
    result = validator.validate_gr_candidate(_parsed(), _match())
    assert result.can_post is True
    assert result.validation_status == "VALID"


def test_quantity_exceeds_open_quantity():
    result = validator.validate_gr_candidate(_parsed(quantity=50.0), _match(open_quantity=40))
    assert result.can_post is False
    assert "QUANTITY_EXCEEDS_OPEN_QTY" in _codes(result)


def test_quantity_missing():
    result = validator.validate_gr_candidate(_parsed(quantity=None), _match())
    assert result.can_post is False
    assert "QUANTITY_MISSING" in _codes(result)


def test_invalid_quantity_zero():
    result = validator.validate_gr_candidate(_parsed(quantity=0), _match())
    assert result.can_post is False
    assert "INVALID_QUANTITY" in _codes(result)


def test_batch_required_missing():
    result = validator.validate_gr_candidate(
        _parsed(batch=None), _match(batch_required=True)
    )
    assert result.can_post is False
    assert "BATCH_REQUIRED_MISSING" in _codes(result)


def test_batch_required_present():
    result = validator.validate_gr_candidate(
        _parsed(batch="LOT123"), _match(batch_required=True)
    )
    assert result.can_post is True


def test_serial_required_missing():
    result = validator.validate_gr_candidate(
        _parsed(quantity=2.0, serial_numbers=[]),
        _match(serial_required=True),
    )
    assert result.can_post is False
    assert "SERIAL_REQUIRED_MISSING" in _codes(result)


def test_serial_count_mismatch():
    result = validator.validate_gr_candidate(
        _parsed(quantity=2.0, serial_numbers=["SN001"]),
        _match(serial_required=True),
    )
    assert result.can_post is False
    assert "SERIAL_COUNT_MISMATCH" in _codes(result)


def test_serial_count_matches():
    result = validator.validate_gr_candidate(
        _parsed(quantity=2.0, serial_numbers=["SN001", "SN002"]),
        _match(serial_required=True),
    )
    assert result.can_post is True


def test_deleted_item_blocked():
    result = validator.validate_gr_candidate(_parsed(), _match(deleted=True))
    assert result.can_post is False
    assert "PO_ITEM_DELETED" in _codes(result)


def test_delivery_completed_blocked():
    result = validator.validate_gr_candidate(_parsed(), _match(delivery_completed=True))
    assert result.can_post is False
    assert "PO_ITEM_DELIVERY_COMPLETED" in _codes(result)


def test_missing_open_quantity_blocks_posting():
    result = validator.validate_gr_candidate(_parsed(), _match(open_quantity=None))
    assert result.can_post is False
    assert "OPEN_QTY_NOT_AVAILABLE_FROM_API" in _codes(result)


def test_po_missing():
    result = validator.validate_gr_candidate(_parsed(po_number=None), MatchResult())
    assert result.can_post is False
    assert "PO_MISSING" in _codes(result)


def test_unit_mismatch():
    result = validator.validate_gr_candidate(_parsed(entry_unit="KG"), _match(unit="EA"))
    assert result.can_post is False
    assert "UNIT_MISMATCH" in _codes(result)


def test_ambiguous_po_item():
    from app.models.schemas import PurchaseOrderItem
    item = PurchaseOrderItem(
        purchase_order_item="00010", material="MAT-1", description="X",
        plant="1010", storage_location="0001",
        order_quantity=10, received_quantity=0, open_quantity=10, unit="EA",
    )
    ambiguous_match = MatchResult(
        matched=False, purchase_order="4500166596", ambiguous=True, candidate_items=[item]
    )
    result = validator.validate_gr_candidate(_parsed(), ambiguous_match)
    assert "PO_ITEM_AMBIGUOUS" in _codes(result)
    assert result.can_post is False
