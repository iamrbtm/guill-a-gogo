from __future__ import annotations

import datetime as dt
import hashlib
import uuid

from sqlalchemy.orm import Session

from app.models.itinerary import ProviderRecord


def fingerprint(provider: str, request: dict) -> str:
    raw = provider + ":" + _stable(request)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _stable(obj) -> str:
    import json

    return json.dumps(obj, sort_keys=True, default=str)


def record_fetch(
    session: Session,
    *,
    provider: str,
    request: dict,
    normalized_response: dict,
    entity_type: str | None = None,
    provider_id: str | None = None,
    ttl_seconds: int | None = None,
    verification_status: str = "unverified",
    source_link: str | None = None,
    trip_id: uuid.UUID | None = None,
    now: dt.datetime | None = None,
) -> ProviderRecord:
    now = now or dt.datetime.now(dt.timezone.utc)
    rec = ProviderRecord(
        trip_id=trip_id,
        provider=provider,
        provider_id=provider_id,
        entity_type=entity_type,
        request_fingerprint=fingerprint(provider, request),
        retrieved_at=now,
        expires_at=now + dt.timedelta(seconds=ttl_seconds) if ttl_seconds else None,
        normalized_response=normalized_response,
        verification_status=verification_status,
        source_link=source_link,
    )
    session.add(rec)
    session.flush()
    return rec


def is_stale(record: ProviderRecord, now: dt.datetime | None = None) -> bool:
    if record.expires_at is None:
        return False
    now = now or dt.datetime.now(dt.timezone.utc)
    exp = record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=dt.timezone.utc)
    return exp <= now


def latest_record(session: Session, provider: str, request: dict, trip_id: uuid.UUID | None = None) -> ProviderRecord | None:
    fp = fingerprint(provider, request)
    q = session.query(ProviderRecord).filter_by(provider=provider, request_fingerprint=fp)
    if trip_id is not None:
        q = q.filter_by(trip_id=trip_id)
    return q.order_by(ProviderRecord.retrieved_at.desc()).first()


def fresh_record(session: Session, provider: str, request: dict, trip_id: uuid.UUID | None = None) -> ProviderRecord | None:
    rec = latest_record(session, provider, request, trip_id)
    if rec is None:
        return None
    return None if is_stale(rec) else rec
