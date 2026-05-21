from __future__ import annotations

import re
import logging
from typing import NamedTuple

from app.models.schemas import ParsedFields, ParsedFieldSource

logger = logging.getLogger(__name__)

PO_PATTERNS: list[tuple[str, str]] = [
    (r"\b(45\d{8})\b", "po_direct_45"),
    (r"\b(55\d{8})\b", "po_direct_55"),
    (r"\bPO[:\s#\-]*(\d{8,12})\b", "po_label_PO"),
    (r"\bP\.?O\.?[:\s#\-]*(\d{8,12})\b", "po_label_PO_dot"),
    (r"\bPURCHASE\s*ORDER[:\s#\-]*(\d{8,12})\b", "po_label_full"),
]

QTY_PATTERNS: list[tuple[str, str, bool]] = [
    (r"\bQTY[:\s]*(\d+(?:\.\d+)?)\s*([A-Z]{1,3})?\b", "qty_label_QTY", True),
    (r"\bQUANTITY[:\s]*(\d+(?:\.\d+)?)\s*([A-Z]{1,3})?\b", "qty_label_QUANTITY", True),
    (r"\b(\d+(?:\.\d+)?)\s*(EA|PC|PCS|KG|G|LB|L|M)\b", "qty_inline_with_unit", False),
]

BATCH_PATTERNS: list[tuple[str, str]] = [
    (r"\bBATCH[:\s#\-]*([A-Z0-9\-]+)\b", "batch_label_BATCH"),
    (r"\bLOT\s*NO[:\s#\-]*([A-Z0-9\-]+)\b", "batch_label_LOT_NO"),
    (r"\bLOT[:\s#\-]*([A-Z0-9\-]+)\b", "batch_label_LOT"),
]

SERIAL_PATTERNS: list[tuple[str, str]] = [
    (r"\bS\/N[:\s#\-]*([A-Z0-9\-]+)\b", "serial_label_SN_slash"),
    (r"\bSN[:\s#\-]*([A-Z0-9\-]+)\b", "serial_label_SN"),
    (r"\bSERIAL[:\s#\-]*([A-Z0-9\-]+)\b", "serial_label_SERIAL"),
]

_UOM_SYNONYMS: dict[str, str] = {
    "PCS": "EA",
    "PC": "EA",
}

_NUMERIC_OCR_FIXES = str.maketrans("OIl", "011")


class _QtyHit(NamedTuple):
    value: float
    unit: str | None
    rule: str
    raw: str


def _normalize_numeric_candidate(text: str) -> str:
    """Apply O→0, I→1, l→1 only inside numeric-looking strings."""
    return text.translate(_NUMERIC_OCR_FIXES)


class ParserService:

    def parse(self, raw_text: str) -> ParsedFields:
        upper = raw_text.upper()
        sources: list[ParsedFieldSource] = []

        po_number, po_candidates, po_ambiguous = self._extract_po(upper, sources)
        quantity, entry_unit, qty_candidates, qty_ambiguous = self._extract_qty(upper, sources)
        batch = self._extract_batch(upper, sources)
        serial_numbers = self._extract_serials(upper, sources)
        material_hint = self._extract_material_hint(upper, po_number, quantity, batch, serial_numbers)

        confidence: dict[str, float] = {
            "po_number": 0.9 if po_number and not po_ambiguous else (0.5 if po_number else 0.0),
            "quantity": 0.9 if quantity and not qty_ambiguous else (0.5 if quantity else 0.0),
            "entry_unit": 0.9 if entry_unit else 0.0,
            "batch": 0.9 if batch else 0.0,
            "serial_numbers": 0.9 if serial_numbers else 0.0,
            "material_text_hint": 0.5 if material_hint else 0.0,
        }

        return ParsedFields(
            po_number=po_number,
            purchase_order_item=None,
            quantity=quantity,
            entry_unit=entry_unit,
            batch=batch,
            serial_numbers=serial_numbers,
            material_text_hint=material_hint,
            field_confidence=confidence,
            source_map=sources,
            ambiguous_po=po_ambiguous,
            ambiguous_quantity=qty_ambiguous,
            po_candidates=po_candidates,
            quantity_candidates=qty_candidates,
        )

    def _extract_po(
        self, upper: str, sources: list[ParsedFieldSource]
    ) -> tuple[str | None, list[str], bool]:
        seen: dict[str, str] = {}  # normalized_value → rule_name

        # Run patterns on both original text and a pre-normalized copy so that
        # common OCR substitutions (O→0, I→1, l→1) inside numeric candidates
        # don't prevent the PO regex from matching.
        normalized_upper = _normalize_numeric_candidate(upper)
        search_pairs = [
            (upper, False),
            (normalized_upper, True),
        ]

        for search_text, was_prenormalized in search_pairs:
            for pattern, rule in PO_PATTERNS:
                for m in re.finditer(pattern, search_text):
                    raw_val = m.group(1)
                    normalized = _normalize_numeric_candidate(raw_val)
                    if normalized not in seen:
                        # Recover original text from same span in upper for audit
                        try:
                            original_raw = upper[m.start(1):m.end(1)]
                        except Exception:
                            original_raw = raw_val
                        seen[normalized] = rule
                        sources.append(
                            ParsedFieldSource(
                                field="po_number",
                                raw_value=original_raw,
                                normalized_value=normalized,
                                rule_name=rule,
                                normalized=was_prenormalized or (normalized != original_raw),
                            )
                        )

        candidates = list(seen.keys())
        if not candidates:
            return None, [], False
        if len(candidates) == 1:
            return candidates[0], candidates, False
        return None, candidates, True

    def _extract_qty(
        self, upper: str, sources: list[ParsedFieldSource]
    ) -> tuple[float | None, str | None, list[float], bool]:
        hits: list[_QtyHit] = []

        for pattern, rule, has_unit_group in QTY_PATTERNS:
            for m in re.finditer(pattern, upper):
                raw_qty = m.group(1)
                raw_unit = m.group(2) if has_unit_group else (m.group(2) if len(m.groups()) >= 2 else None)
                norm_qty = _normalize_numeric_candidate(raw_qty)
                try:
                    qty_val = float(norm_qty)
                except ValueError:
                    continue
                unit_val = _UOM_SYNONYMS.get(raw_unit, raw_unit) if raw_unit else None
                hits.append(_QtyHit(qty_val, unit_val, rule, raw_qty))
                sources.append(
                    ParsedFieldSource(
                        field="quantity",
                        raw_value=raw_qty,
                        normalized_value=norm_qty,
                        rule_name=rule,
                        normalized=(norm_qty != raw_qty),
                    )
                )
                if raw_unit:
                    sources.append(
                        ParsedFieldSource(
                            field="entry_unit",
                            raw_value=raw_unit,
                            normalized_value=unit_val,
                            rule_name=rule,
                            normalized=False,
                        )
                    )

        if not hits:
            return None, None, [], False

        # Deduplicate by value
        unique_vals: list[float] = []
        seen_vals: set[float] = set()
        for h in hits:
            if h.value not in seen_vals:
                seen_vals.add(h.value)
                unique_vals.append(h.value)

        if len(unique_vals) > 1:
            return None, None, unique_vals, True

        best = hits[0]
        unit = None
        for h in hits:
            if h.unit:
                unit = h.unit
                break
        return best.value, unit, unique_vals, False

    def _extract_batch(self, upper: str, sources: list[ParsedFieldSource]) -> str | None:
        for pattern, rule in BATCH_PATTERNS:
            m = re.search(pattern, upper)
            if m:
                val = m.group(1)
                sources.append(
                    ParsedFieldSource(
                        field="batch",
                        raw_value=val,
                        normalized_value=val,
                        rule_name=rule,
                        normalized=False,
                    )
                )
                return val
        return None

    def _extract_serials(self, upper: str, sources: list[ParsedFieldSource]) -> list[str]:
        seen: list[str] = []
        seen_set: set[str] = set()
        for pattern, rule in SERIAL_PATTERNS:
            for m in re.finditer(pattern, upper):
                val = m.group(1)
                if val not in seen_set:
                    seen_set.add(val)
                    seen.append(val)
                    sources.append(
                        ParsedFieldSource(
                            field="serial_numbers",
                            raw_value=val,
                            normalized_value=val,
                            rule_name=rule,
                            normalized=False,
                        )
                    )
        return seen

    def _extract_material_hint(
        self,
        upper: str,
        po_number: str | None,
        quantity: float | None,
        batch: str | None,
        serials: list[str],
    ) -> str | None:
        used_tokens: set[str] = set()
        if po_number:
            used_tokens.add(po_number)
        if batch:
            used_tokens.add(batch)
        for sn in serials:
            used_tokens.add(sn)

        candidates: list[str] = []
        for line in upper.splitlines():
            line = line.strip()
            if not line:
                continue
            # Skip lines that contain PO numbers or qty tokens
            if any(tok in line for tok in used_tokens):
                continue
            if re.search(r"\b(?:PO|QTY|QUANTITY|LOT|BATCH|SERIAL|SN|S\/N)[:\s]", line):
                continue
            if re.search(r"\b45\d{8}\b|\b55\d{8}\b", line):
                continue
            # Keep lines that look like descriptive uppercase text (2+ alpha words)
            words = re.findall(r"[A-Z]{2,}", line)
            if len(words) >= 2:
                candidates.append(line)

        return " ".join(candidates[:3]).strip() if candidates else None
