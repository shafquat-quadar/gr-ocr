from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from app.sap.sap_adapter import SAPAdapter

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_PO_FILE = _DATA_DIR / "mock_purchase_orders.json"
_MAT_DOC_FILE = _DATA_DIR / "mock_material_documents.json"

_MATDOC_COUNTER_START = 5000000001


class MockSAPAdapter(SAPAdapter):

    def get_purchase_order(self, po_number: str) -> dict:
        data = self._load_pos()
        for po in data.get("purchase_orders", []):
            if po["purchase_order"] == po_number:
                logger.info("Mock SAP: found PO %s", po_number)
                return po
        raise KeyError(f"Purchase order {po_number!r} not found in mock data")

    def post_goods_receipt(self, payload: dict) -> dict:
        po_number = payload.get("purchase_order", "")
        po_item = payload.get("purchase_order_item", "")
        quantity = payload.get("quantity")
        if not po_number or not po_item or not quantity:
            raise ValueError("Mock SAP: payload missing required fields (purchase_order, purchase_order_item, quantity)")

        mat_doc_number = self._next_material_document()
        year = str(datetime.now(timezone.utc).year)
        record = {
            "material_document": mat_doc_number,
            "material_document_year": year,
            "purchase_order": po_number,
            "purchase_order_item": po_item,
            "quantity": quantity,
            "entry_unit": payload.get("entry_unit", "EA"),
            "movement_type": payload.get("movement_type", "101"),
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "status": "POSTED",
            "message": "Mock material document posted successfully",
        }
        self._append_material_document(record)
        logger.info("Mock SAP: posted GR → material document %s / %s", mat_doc_number, year)
        return {
            "material_document": mat_doc_number,
            "material_document_year": year,
            "status": "POSTED",
            "message": "Mock material document posted successfully",
        }

    def get_material_document(self, material_document: str, year: str) -> dict:
        data = self._load_mat_docs()
        for doc in data.get("material_documents", []):
            if doc["material_document"] == material_document and doc.get("material_document_year") == year:
                return doc
        raise KeyError(f"Material document {material_document}/{year} not found in mock data")

    def ping(self) -> dict:
        return {"sap_mode": "mock", "status": "ok"}

    def _load_pos(self) -> dict:
        with open(_PO_FILE, encoding="utf-8") as fh:
            return json.load(fh)

    def _load_mat_docs(self) -> dict:
        if not _MAT_DOC_FILE.exists():
            return {"material_documents": []}
        with open(_MAT_DOC_FILE, encoding="utf-8") as fh:
            return json.load(fh)

    def _save_mat_docs(self, data: dict) -> None:
        with open(_MAT_DOC_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    def _next_material_document(self) -> str:
        data = self._load_mat_docs()
        docs = data.get("material_documents", [])
        if not docs:
            return str(_MATDOC_COUNTER_START)
        numbers = []
        for d in docs:
            try:
                numbers.append(int(d["material_document"]))
            except (KeyError, ValueError):
                pass
        return str(max(numbers) + 1) if numbers else str(_MATDOC_COUNTER_START)

    def _append_material_document(self, record: dict) -> None:
        data = self._load_mat_docs()
        data.setdefault("material_documents", []).append(record)
        self._save_mat_docs(data)
