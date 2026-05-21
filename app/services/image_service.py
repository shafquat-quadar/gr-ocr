from __future__ import annotations

import hashlib
import logging
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
_COUNTER_FILE = Path(settings.UPLOAD_DIR) / ".request_counter"


def _next_request_id() -> str:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    try:
        current = int(_COUNTER_FILE.read_text().strip()) if _COUNTER_FILE.exists() else 0
    except ValueError:
        current = 0
    current += 1
    _COUNTER_FILE.write_text(str(current))
    return f"REQ-{current:06d}"


class ImageService:

    def validate_and_save(self, file: UploadFile) -> dict:
        content_type = file.content_type or ""
        if content_type not in settings.allowed_mime_types:
            raise HTTPException(
                status_code=415,
                detail={
                    "error": {
                        "code": "INVALID_FILE_TYPE",
                        "message": f"Unsupported content type {content_type!r}. Allowed: {settings.ALLOWED_IMAGE_TYPES}",
                    }
                },
            )

        suffix = Path(file.filename or "image.jpg").suffix.lower()
        if suffix not in _ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail={
                    "error": {
                        "code": "INVALID_FILE_EXTENSION",
                        "message": f"Unsupported extension {suffix!r}. Allowed: {_ALLOWED_EXTENSIONS}",
                    }
                },
            )

        data = file.file.read()
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": f"File exceeds maximum size of {settings.MAX_UPLOAD_MB} MB.",
                    }
                },
            )

        sha256 = hashlib.sha256(data).hexdigest()
        request_id = _next_request_id()

        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / f"{request_id}{suffix}"
        dest.write_bytes(data)

        logger.info("Saved image for %s → %s (sha256=%s...)", request_id, dest, sha256[:8])
        return {
            "request_id": request_id,
            "image_uri": str(dest),
            "image_sha256": sha256,
            "filename": file.filename,
            "content_type": content_type,
            "size_bytes": len(data),
        }
