from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np
import pytesseract
from PIL import Image

from app.config import get_settings
from app.models.schemas import OCRResult

logger = logging.getLogger(__name__)
settings = get_settings()

# Patterns used to score parser-readiness
_PO_RE = re.compile(r"\b(?:45|55)\d{8}\b|\bPO[:\s#\-]*\d{6,}\b", re.IGNORECASE)
_QTY_RE = re.compile(r"\bQTY[:\s]*\d|\bQUANTITY[:\s]*\d|\b\d+\s*(?:EA|PC|PCS|KG|LB)\b", re.IGNORECASE)
_BATCH_RE = re.compile(r"\b(?:BATCH|LOT)[:\s#\-]*[A-Z0-9\-]+", re.IGNORECASE)
_SERIAL_RE = re.compile(r"\b(?:S\/N|SN|SERIAL)[:\s#\-]*[A-Z0-9\-]+", re.IGNORECASE)
_UPPER_WORDS_RE = re.compile(r"\b[A-Z]{3,}\b")


@dataclass
class _Candidate:
    variant: str
    psm: int
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


def _score_text(text: str) -> float:
    score = 0.0
    if _PO_RE.search(text):
        score += 5
    if _QTY_RE.search(text):
        score += 5
    if _BATCH_RE.search(text):
        score += 2
    if _SERIAL_RE.search(text):
        score += 2
    upper_words = _UPPER_WORDS_RE.findall(text)
    if upper_words:
        score += 1
    return score


def _run_tesseract(image: np.ndarray, psm: int, lang: str = "eng") -> str:
    pil_img = Image.fromarray(image)
    config = f"--psm {psm} --oem 3"
    return pytesseract.image_to_string(pil_img, lang=lang, config=config)


def _preprocess_variants(bgr: np.ndarray) -> dict[str, np.ndarray]:
    variants: dict[str, np.ndarray] = {}
    variants["original"] = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    variants["grayscale"] = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    h, w = gray.shape[:2]
    resized = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    variants["resized_2x"] = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants["thresholded"] = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)

    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh_dn = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants["denoised_threshold"] = cv2.cvtColor(thresh_dn, cv2.COLOR_GRAY2RGB)

    return variants


class OCRService:

    def __init__(self) -> None:
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    def extract_text(self, image_path: str) -> OCRResult:
        bgr = cv2.imread(image_path)
        if bgr is None:
            raise ValueError(f"Cannot read image at {image_path!r}")

        variants = _preprocess_variants(bgr)
        candidates: list[_Candidate] = []

        for variant_name, img_array in variants.items():
            for psm in (6, 11):
                try:
                    text = _run_tesseract(img_array, psm)
                    score = _score_text(text)
                    candidates.append(
                        _Candidate(
                            variant=variant_name,
                            psm=psm,
                            text=text,
                            score=score,
                            metadata={"variant": variant_name, "psm": psm},
                        )
                    )
                except Exception as exc:
                    logger.warning("OCR failed for variant=%s psm=%d: %s", variant_name, psm, exc)

        if not candidates:
            raise RuntimeError("All OCR attempts failed for image")

        best = max(candidates, key=lambda c: c.score)
        logger.info(
            "Best OCR candidate: variant=%s psm=%d score=%.1f text_len=%d",
            best.variant,
            best.psm,
            best.score,
            len(best.text),
        )

        debug = {
            "best_variant": best.variant,
            "best_psm": best.psm,
            "all_scores": [
                {"variant": c.variant, "psm": c.psm, "score": c.score}
                for c in candidates
            ],
        }

        return OCRResult(
            raw_text=best.text.strip(),
            engine="tesseract",
            overall_confidence=None,
            debug_metadata=debug,
        )
