from __future__ import annotations

import json

from app.db import get_session
from app.models import AuditEvent


def audit(report_id: str, event_type: str, details: dict) -> None:
    with get_session() as session:
        session.add(
            AuditEvent(report_id=report_id, event_type=event_type, details_json=json.dumps(details))
        )
        session.commit()
