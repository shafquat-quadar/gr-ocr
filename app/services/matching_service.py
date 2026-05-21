from __future__ import annotations

import logging

from rapidfuzz import fuzz

from app.models.schemas import MatchResult, ParsedFields, PurchaseOrder, PurchaseOrderItem

logger = logging.getLogger(__name__)

_STRONG_THRESHOLD = 90
_POSSIBLE_THRESHOLD = 75


class MatchingService:

    def match_po_item(self, parsed: ParsedFields, po: PurchaseOrder) -> MatchResult:
        open_items = [it for it in po.items if not it.deleted and not it.delivery_completed]

        # 1. User explicitly provided a PO item number
        if parsed.purchase_order_item:
            return self._match_by_item_number(parsed.purchase_order_item, po)

        # 2. Only one open item — auto-select
        if len(open_items) == 1:
            item = open_items[0]
            logger.info("Single open PO item — auto-selecting %s", item.purchase_order_item)
            return _to_match_result(po.purchase_order, item, match_method="single_open_item", score=100.0)

        # 3. Material number found in OCR hints matching a PO item
        if parsed.material_text_hint:
            material_match = self._match_by_material(parsed.material_text_hint, open_items)
            if material_match:
                return _to_match_result(po.purchase_order, material_match, match_method="material_ocr_hint")

        # 4. Fuzzy description matching
        if parsed.material_text_hint and open_items:
            result = self._match_by_description(parsed.material_text_hint, po.purchase_order, open_items)
            if result:
                return result

        # 5. Ambiguous — need human correction
        logger.info("No clear PO item match — returning candidates")
        return MatchResult(
            matched=False,
            purchase_order=po.purchase_order,
            ambiguous=True,
            candidate_items=open_items,
            match_method="ambiguous",
        )

    def _match_by_item_number(self, item_number: str, po: PurchaseOrder) -> MatchResult:
        normalized = item_number.zfill(5)
        for item in po.items:
            if item.purchase_order_item.zfill(5) == normalized:
                return _to_match_result(po.purchase_order, item, match_method="exact_item_number", score=100.0)
        return MatchResult(
            matched=False,
            purchase_order=po.purchase_order,
            ambiguous=False,
            match_method="exact_item_number_not_found",
        )

    def _match_by_material(self, hint: str, open_items: list[PurchaseOrderItem]) -> PurchaseOrderItem | None:
        hint_upper = hint.upper()
        for item in open_items:
            if item.material.upper() in hint_upper or hint_upper in item.material.upper():
                return item
        return None

    def _match_by_description(
        self, hint: str, po_number: str, open_items: list[PurchaseOrderItem]
    ) -> MatchResult | None:
        scores: list[tuple[float, PurchaseOrderItem]] = []
        for item in open_items:
            score = fuzz.token_set_ratio(hint.upper(), item.description.upper())
            scores.append((score, item))

        scores.sort(key=lambda x: x[0], reverse=True)
        if not scores:
            return None

        best_score, best_item = scores[0]
        logger.info("Best fuzzy match: %s → %s (score=%s)", hint, best_item.description, best_score)

        if best_score < _POSSIBLE_THRESHOLD:
            return MatchResult(
                matched=False,
                purchase_order=po_number,
                ambiguous=True,
                candidate_items=open_items,
                match_method="fuzzy_description_weak",
                match_score=best_score,
            )

        # Check if multiple items have similar high scores (within 5 points)
        if best_score >= _STRONG_THRESHOLD and len(scores) > 1:
            close_runners = [it for sc, it in scores[1:] if sc >= best_score - 5]
            if close_runners:
                return MatchResult(
                    matched=False,
                    purchase_order=po_number,
                    ambiguous=True,
                    candidate_items=[best_item] + close_runners,
                    match_method="fuzzy_description_ambiguous",
                    match_score=best_score,
                )

        if best_score >= _STRONG_THRESHOLD:
            return _to_match_result(po_number, best_item, match_method="fuzzy_description_strong", score=best_score)

        # Possible match — still requires confirmation but we surface it
        return MatchResult(
            matched=False,
            purchase_order=po_number,
            purchase_order_item=best_item.purchase_order_item,
            material=best_item.material,
            description=best_item.description,
            plant=best_item.plant,
            storage_location=best_item.storage_location,
            order_quantity=best_item.order_quantity,
            received_quantity=best_item.received_quantity,
            open_quantity=best_item.open_quantity,
            unit=best_item.unit,
            batch_required=best_item.batch_required,
            serial_required=best_item.serial_required,
            ambiguous=True,
            candidate_items=open_items,
            match_method="fuzzy_description_possible",
            match_score=best_score,
        )


def _to_match_result(
    po_number: str, item: PurchaseOrderItem, match_method: str, score: float | None = None
) -> MatchResult:
    return MatchResult(
        matched=True,
        purchase_order=po_number,
        purchase_order_item=item.purchase_order_item,
        material=item.material,
        description=item.description,
        plant=item.plant,
        storage_location=item.storage_location,
        order_quantity=item.order_quantity,
        received_quantity=item.received_quantity,
        open_quantity=item.open_quantity,
        unit=item.unit,
        batch_required=item.batch_required,
        serial_required=item.serial_required,
        deleted=item.deleted,
        delivery_completed=item.delivery_completed,
        match_method=match_method,
        match_score=score,
        ambiguous=False,
        candidate_items=[],
    )
