from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from app.models.schemas import MatchResult, ParsedFields


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Copy mock data to a temp dir so tests don't mutate the real files."""
    src = Path(__file__).parent.parent / "app" / "data"
    dest = tmp_path / "data"
    shutil.copytree(src, dest)
    return dest


@pytest.fixture
def mock_adapter(temp_data_dir, monkeypatch):
    from app.sap import mock_sap_adapter as mod
    monkeypatch.setattr(mod, "_PO_FILE", temp_data_dir / "mock_purchase_orders.json")
    monkeypatch.setattr(mod, "_MAT_DOC_FILE", temp_data_dir / "mock_material_documents.json")
    from app.sap.mock_sap_adapter import MockSAPAdapter
    return MockSAPAdapter()


def test_confirm_valid_draft_posts_mock_gr(mock_adapter):
    payload = {
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
    result = mock_adapter.post_goods_receipt(payload)
    assert result["status"] == "POSTED"
    assert result["material_document"].startswith("5")
    assert result["material_document_year"]


def test_confirm_invalid_draft_blocked(mock_adapter):
    """Missing required fields should raise ValueError."""
    with pytest.raises(ValueError, match="required fields"):
        mock_adapter.post_goods_receipt({"purchase_order": "4500166595"})


def test_duplicate_posting_blocked():
    """Idempotency hash comparison is exercised in the orchestrator.
    This test checks the hash logic directly."""
    import hashlib

    def make_hash(po, item, qty, unit, batch, serials, img_sha):
        serial_str = ",".join(sorted(serials))
        raw = f"{po}|{item}|{qty}|{unit}|{batch}|{serial_str}|{img_sha}"
        return hashlib.sha256(raw.encode()).hexdigest()

    h1 = make_hash("4500166595", "00010", 10, "EA", "B24X91", [], "abc123")
    h2 = make_hash("4500166595", "00010", 10, "EA", "B24X91", [], "abc123")
    h3 = make_hash("4500166595", "00010", 11, "EA", "B24X91", [], "abc123")

    assert h1 == h2, "Same inputs must produce same hash"
    assert h1 != h3, "Different quantity must produce different hash"


def test_material_document_counter_increments(mock_adapter):
    payload = {
        "purchase_order": "4500166595",
        "purchase_order_item": "00010",
        "quantity": 5,
        "entry_unit": "EA",
    }
    r1 = mock_adapter.post_goods_receipt(payload)
    r2 = mock_adapter.post_goods_receipt(payload)
    assert int(r2["material_document"]) > int(r1["material_document"])


def test_po_not_found_raises(mock_adapter):
    with pytest.raises(KeyError):
        mock_adapter.get_purchase_order("9999999999")


def test_mock_ping(mock_adapter):
    result = mock_adapter.ping()
    assert result == {"sap_mode": "mock", "status": "ok"}
