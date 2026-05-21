from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.db_models import AuditEvent
from app.models.schemas import AuditEventResponse

logger = logging.getLogger(__name__)


class AuditService:

    def create_event(
        self,
        db: Session,
        request_id: str,
        event_type: str,
        actor_type: str = "system",
        actor_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            request_id=request_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            payload_json=json.dumps(payload or {}, default=str),
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.flush()
        logger.info("Audit [%s] %s actor=%s/%s", request_id, event_type, actor_type, actor_id)
        return event

    def get_events(self, db: Session, request_id: str) -> list[AuditEventResponse]:
        events = (
            db.query(AuditEvent)
            .filter(AuditEvent.request_id == request_id)
            .order_by(AuditEvent.created_at.asc())
            .all()
        )
        results = []
        for ev in events:
            try:
                payload = json.loads(ev.payload_json)
            except Exception:
                payload = {}
            results.append(
                AuditEventResponse(
                    id=ev.id,
                    request_id=ev.request_id,
                    event_type=ev.event_type,
                    actor_type=ev.actor_type,
                    actor_id=ev.actor_id,
                    payload=payload,
                    created_at=ev.created_at,
                )
            )
        return results
