from __future__ import annotations

import logging

from app.sap.sap_adapter import SAPAdapter
from app.sap.sap_client import SAPODataClient, SAPODataError

logger = logging.getLogger(__name__)

_PO_SERVICE = "API_PURCHASEORDER_PROCESS_SRV"
_MATDOC_SERVICE = "API_MATERIAL_DOCUMENT_SRV"


class RealSAPODataAdapter(SAPAdapter):

    def __init__(self, client: SAPODataClient, sap_client_code: str = ""):
        self._client = client
        self._sap_client_code = sap_client_code

    def get_purchase_order(self, po_number: str) -> dict:
        path = f"{_PO_SERVICE}/A_PurchaseOrder('{po_number}')"
        params = {"$expand": "to_PurchaseOrderItem"}
        raw = self._client.get(path, params=params)
        return self._normalize_po(raw.get("d", raw))

    def post_goods_receipt(self, payload: dict) -> dict:
        sap_payload = _map_to_sap_matdoc_payload(payload)
        service_root = f"{_MATDOC_SERVICE}/"
        entity_path = f"{_MATDOC_SERVICE}/A_MaterialDocumentHeader"
        raw = self._client.post(service_root, entity_path, sap_payload)
        return _normalize_matdoc_response(raw.get("d", raw))

    def get_material_document(self, material_document: str, year: str) -> dict:
        path = (
            f"{_MATDOC_SERVICE}/A_MaterialDocumentHeader"
            f"(MaterialDocumentYear='{year}',MaterialDocument='{material_document}')"
        )
        raw = self._client.get(path)
        return raw.get("d", raw)

    def ping(self) -> dict:
        result = self._client.ping()
        return {
            "sap_mode": "real",
            "status": "ok" if result.get("reachable") else "unreachable",
            "material_document_service_reachable": result.get("reachable", False),
        }

    def _normalize_po(self, raw: dict) -> dict:
        items_raw = raw.get("to_PurchaseOrderItem", {})
        if isinstance(items_raw, dict):
            items_raw = items_raw.get("results", [])

        items = []
        for it in items_raw:
            order_qty = _safe_float(it.get("OrderQuantity"))
            received_qty = _safe_float(it.get("GoodsReceiptQuantity") or it.get("ReceivedQuantity") or "0")
            if order_qty is not None and received_qty is not None:
                open_qty: float | None = max(0.0, order_qty - received_qty)
            else:
                open_qty = None

            deleted_raw = it.get("PurchaseOrderItemDeletionInd") or it.get("DeletionIndicator") or ""
            completed_raw = it.get("IsCompletelyDelivered") or it.get("DeliveryCompletedQuantity")

            # TODO: Production should derive batch_required / serial_required from
            # material master / plant data (MM60, serial number profile) rather than
            # defaulting false here. The PO OData API does not expose these flags directly.
            items.append({
                "purchase_order_item": it.get("PurchaseOrderItem", ""),
                "material": it.get("Material", ""),
                "description": it.get("PurchaseOrderItemText") or it.get("ShortText") or "",
                "plant": it.get("Plant", ""),
                "storage_location": it.get("StorageLocation") or "",
                "order_quantity": order_qty,
                "received_quantity": received_qty,
                "open_quantity": open_qty,
                "unit": it.get("PurchaseOrderQuantityUnit") or it.get("OrderPriceUnit") or "",
                "batch_required": False,
                "serial_required": False,
                "deleted": str(deleted_raw).upper() in ("X", "TRUE", "1"),
                "delivery_completed": bool(completed_raw),
            })

        return {
            "purchase_order": raw.get("PurchaseOrder", ""),
            "supplier": raw.get("Supplier") or raw.get("Vendor") or "",
            "company_code": raw.get("CompanyCode", ""),
            "items": items,
        }


def _safe_float(val: object) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _map_to_sap_matdoc_payload(payload: dict) -> dict:
    posting_date = _fmt_date(payload.get("posting_date"))
    document_date = _fmt_date(payload.get("document_date"))
    quantity_str = str(payload.get("quantity", ""))
    batch = payload.get("batch") or ""
    serial_numbers: list[str] = payload.get("serial_numbers") or []
    request_id = payload.get("header_text", "")

    item: dict = {
        "MaterialDocumentLine": "0001",
        "Material": payload.get("material", ""),
        "Plant": payload.get("plant", ""),
        "GoodsMovementType": payload.get("movement_type", "101"),
        "GoodsMovementRefDocType": "B",
        "PurchaseOrder": payload.get("purchase_order", ""),
        "PurchaseOrderItem": payload.get("purchase_order_item", ""),
        "EntryUnit": payload.get("entry_unit", "EA"),
        "QuantityInEntryUnit": quantity_str,
    }

    storage_location = payload.get("storage_location") or ""
    if storage_location:
        item["StorageLocation"] = storage_location

    if batch:
        item["Batch"] = batch

    if serial_numbers:
        item["to_SerialNumbers"] = {
            "results": [{"SerialNumber": sn} for sn in serial_numbers]
        }

    return {
        "PostingDate": posting_date,
        "DocumentDate": document_date,
        "MaterialDocumentHeaderText": request_id,
        "GoodsMovementCode": payload.get("goods_movement_code", "01"),
        "to_MaterialDocumentItem": {"results": [item]},
    }


def _fmt_date(val: object) -> str:
    if val is None:
        from datetime import date
        return date.today().strftime("%Y-%m-%dT00:00:00")
    s = str(val)
    if "T" in s:
        return s
    return f"{s}T00:00:00"


def _normalize_matdoc_response(raw: dict) -> dict:
    return {
        "material_document": raw.get("MaterialDocument", ""),
        "material_document_year": raw.get("MaterialDocumentYear", ""),
        "status": "POSTED",
        "message": "SAP material document posted successfully",
    }
