from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.accounts import AuditEvent


def record_audit(
    session: Session,
    *,
    action: str,
    actor_user_id: Optional[uuid.UUID] = None,
    object_type: Optional[str] = None,
    object_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    meta: Optional[dict] = None,
) -> None:
    """Append an audit event. Best-effort; never raises to the caller."""
    try:
        session.add(
            AuditEvent(
                actor_user_id=actor_user_id,
                action=action,
                object_type=object_type,
                object_id=object_id,
                ip_address=ip_address,
                meta=meta,
            )
        )
        session.flush()
    except Exception:  # pragma: no cover - audit must not break the request
        import logging

        logging.getLogger("guill.audit").exception("failed to record audit event")
