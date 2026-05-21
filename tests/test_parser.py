from __future__ import annotations

import pytest

from app.services.parser_service import ParserService

parser = ParserService()


def test_extract_po_number():
    result = parser.parse("PO: 4500166595\nQTY: 10 EA")
    assert result.po_number == "4500166595"
    assert not result.ambiguous_po


def test_extract_po_number_direct():
    result = parser.parse("4500166595\nQTY 5 EA")
    assert result.po_number == "4500166595"


def test_extract_quantity():
    result = parser.parse("PO 4500166596\nQTY: 25 EA")
    assert result.quantity == 25.0
    assert result.entry_unit == "EA"


def test_extract_quantity_inline():
    result = parser.parse("Some text\n15 KG\nother")
    assert result.quantity == 15.0
    assert result.entry_unit == "KG"


def test_extract_batch():
    result = parser.parse("PO 4500166595\nLOT: B24X91\nQTY 10 EA")
    assert result.batch == "B24X91"


def test_extract_batch_lot_no():
    result = parser.parse("LOT NO: XYZ-2024\nQTY 5 EA")
    assert result.batch == "XYZ-2024"


def test_extract_serials():
    result = parser.parse("PO 4500166597\nQTY 2 EA\nSN: SN10001\nSN: SN10002")
    assert "SN10001" in result.serial_numbers
    assert "SN10002" in result.serial_numbers
    assert len(result.serial_numbers) == 2


def test_extract_serials_serial_label():
    result = parser.parse("SERIAL: ABC123\nQTY 1 EA")
    assert "ABC123" in result.serial_numbers


def test_ocr_common_numeric_correction():
    # O→0 correction inside a PO candidate
    result = parser.parse("PO: 45OO166595\nQTY 10 EA")
    # After normalization 45OO166595 → 4500166595
    assert result.po_number == "4500166595"
    # Check that source_map recorded the normalization
    po_sources = [s for s in result.source_map if s.field == "po_number"]
    assert any(s.normalized for s in po_sources)


def test_multiple_po_candidates_needs_correction():
    result = parser.parse("PO 4500166595\nPO 4500166596\nQTY 10 EA")
    assert result.ambiguous_po is True
    assert result.po_number is None
    assert len(result.po_candidates) == 2


def test_multiple_quantity_candidates_needs_correction():
    result = parser.parse("QTY: 10 EA\n15 KG\nPO 4500166595")
    assert result.ambiguous_quantity is True
    assert result.quantity is None
    assert len(result.quantity_candidates) >= 2


def test_material_hint_extracted():
    result = parser.parse("PO 4500166595\nQTY 10 EA\nLOT B24X91\nPRESSURE SENSOR ASSEMBLY")
    assert result.material_text_hint is not None
    assert "PRESSURE" in result.material_text_hint or "SENSOR" in result.material_text_hint


def test_no_po_returns_none():
    result = parser.parse("QTY 5 EA\nSome random text")
    assert result.po_number is None


def test_po_label_purchase_order():
    result = parser.parse("PURCHASE ORDER: 4500166597\nQTY 3 EA")
    assert result.po_number == "4500166597"
