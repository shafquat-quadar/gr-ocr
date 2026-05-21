from __future__ import annotations

import pytest

from app.sap.real_sap_odata_adapter import _map_to_sap_matdoc_payload


def _canonical(**kwargs) -> dict:
    base = {
        "movement_type": "101",
        "goods_movement_code": "01",
        "purchase_order": "4500166595",
        "purchase_order_item": "00010",
        "material": "MAT-100001",
        "plant": "1010",
        "storage_location": "0001",
        "quantity": 10,
        "entry_unit": "EA",
        "batch": "B24X91",
        "serial_numbers": [],
        "posting_date": "2026-05-21",
        "document_date": "2026-05-21",
        "header_text": "GR via OCR agent REQ-000001",
    }
    base.update(kwargs)
    return base


def test_canonical_maps_correctly():
    sap = _map_to_sap_matdoc_payload(_canonical())
    assert sap["GoodsMovementCode"] == "01"
    assert sap["MaterialDocumentHeaderText"] == "GR via OCR agent REQ-000001"
    item = sap["to_MaterialDocumentItem"]["results"][0]
    assert item["PurchaseOrder"] == "4500166595"
    assert item["PurchaseOrderItem"] == "00010"
    assert item["Material"] == "MAT-100001"
    assert item["Plant"] == "1010"
    assert item["StorageLocation"] == "0001"
    assert item["EntryUnit"] == "EA"
    assert item["Batch"] == "B24X91"


def test_batch_omitted_when_empty():
    sap = _map_to_sap_matdoc_payload(_canonical(batch=""))
    item = sap["to_MaterialDocumentItem"]["results"][0]
    assert "Batch" not in item


def test_batch_omitted_when_none():
    sap = _map_to_sap_matdoc_payload(_canonical(batch=None))
    item = sap["to_MaterialDocumentItem"]["results"][0]
    assert "Batch" not in item


def test_serial_numbers_mapped():
    sap = _map_to_sap_matdoc_payload(_canonical(serial_numbers=["SN10001", "SN10002"]))
    item = sap["to_MaterialDocumentItem"]["results"][0]
    assert "to_SerialNumbers" in item
    sns = [r["SerialNumber"] for r in item["to_SerialNumbers"]["results"]]
    assert sns == ["SN10001", "SN10002"]


def test_posting_date_formatted():
    sap = _map_to_sap_matdoc_payload(_canonical(posting_date="2026-05-21"))
    assert sap["PostingDate"] == "2026-05-21T00:00:00"


def test_document_date_formatted():
    sap = _map_to_sap_matdoc_payload(_canonical(document_date="2026-05-21"))
    assert sap["DocumentDate"] == "2026-05-21T00:00:00"


def test_goods_movement_code_is_01():
    sap = _map_to_sap_matdoc_payload(_canonical())
    assert sap["GoodsMovementCode"] == "01"


def test_goods_movement_type_is_101():
    sap = _map_to_sap_matdoc_payload(_canonical())
    item = sap["to_MaterialDocumentItem"]["results"][0]
    assert item["GoodsMovementType"] == "101"


def test_goods_movement_ref_doc_type_is_B():
    sap = _map_to_sap_matdoc_payload(_canonical())
    item = sap["to_MaterialDocumentItem"]["results"][0]
    assert item["GoodsMovementRefDocType"] == "B"


def test_quantity_in_entry_unit_is_string():
    sap = _map_to_sap_matdoc_payload(_canonical(quantity=10))
    item = sap["to_MaterialDocumentItem"]["results"][0]
    assert isinstance(item["QuantityInEntryUnit"], str)
    assert item["QuantityInEntryUnit"] == "10"


def test_no_serial_numbers_no_key():
    sap = _map_to_sap_matdoc_payload(_canonical(serial_numbers=[]))
    item = sap["to_MaterialDocumentItem"]["results"][0]
    assert "to_SerialNumbers" not in item
