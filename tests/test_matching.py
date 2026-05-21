from __future__ import annotations

import pytest

from app.models.schemas import ParsedFields, PurchaseOrder, PurchaseOrderItem
from app.services.matching_service import MatchingService

matcher = MatchingService()

_ITEM_A = PurchaseOrderItem(
    purchase_order_item="00010",
    material="MAT-100001",
    description="PRESSURE SENSOR ASSEMBLY",
    plant="1010",
    storage_location="0001",
    order_quantity=100,
    received_quantity=60,
    open_quantity=40,
    unit="EA",
    batch_required=True,
    serial_required=False,
)

_ITEM_B = PurchaseOrderItem(
    purchase_order_item="00020",
    material="MAT-100002",
    description="CONTROL VALVE ASSEMBLY",
    plant="1010",
    storage_location="0001",
    order_quantity=50,
    received_quantity=0,
    open_quantity=50,
    unit="EA",
)

_PO_SINGLE = PurchaseOrder(
    purchase_order="4500166595",
    items=[_ITEM_A],
)

_PO_MULTI = PurchaseOrder(
    purchase_order="4500166596",
    items=[_ITEM_A, _ITEM_B],
)


def _parsed(**kwargs) -> ParsedFields:
    defaults = dict(po_number="4500166595", quantity=10.0, entry_unit="EA")
    defaults.update(kwargs)
    return ParsedFields(**defaults)


def test_single_open_item_auto_match():
    parsed = _parsed()
    result = matcher.match_po_item(parsed, _PO_SINGLE)
    assert result.matched is True
    assert result.purchase_order_item == "00010"
    assert result.match_method == "single_open_item"


def test_description_match():
    parsed = _parsed(material_text_hint="PRESSURE SENSOR ASSEMBLY", po_number="4500166596")
    result = matcher.match_po_item(parsed, _PO_MULTI)
    assert result.matched is True
    assert result.purchase_order_item == "00010"


def test_ambiguous_items_return_candidates():
    # No description hint, multiple open items → ambiguous
    parsed = _parsed(material_text_hint=None, po_number="4500166596")
    result = matcher.match_po_item(parsed, _PO_MULTI)
    assert result.matched is False
    assert result.ambiguous is True
    assert len(result.candidate_items) == 2


def test_user_selected_item_exact_match():
    parsed = _parsed(purchase_order_item="00020", po_number="4500166596")
    result = matcher.match_po_item(parsed, _PO_MULTI)
    assert result.matched is True
    assert result.purchase_order_item == "00020"
    assert result.match_method == "exact_item_number"


def test_user_selected_nonexistent_item():
    parsed = _parsed(purchase_order_item="00099")
    result = matcher.match_po_item(parsed, _PO_SINGLE)
    assert result.matched is False
    assert result.match_method == "exact_item_number_not_found"


def test_deleted_item_not_in_candidates():
    deleted_item = PurchaseOrderItem(
        purchase_order_item="00010",
        material="MAT-DEL",
        description="DELETED ITEM",
        plant="1010",
        storage_location="0001",
        order_quantity=10,
        received_quantity=0,
        open_quantity=10,
        unit="EA",
        deleted=True,
    )
    po = PurchaseOrder(purchase_order="4500000001", items=[deleted_item])
    parsed = _parsed(po_number="4500000001")
    result = matcher.match_po_item(parsed, po)
    # No open items → ambiguous with empty candidates
    assert result.matched is False
