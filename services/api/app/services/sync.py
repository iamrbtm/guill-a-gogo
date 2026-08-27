from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounts import Trip
from app.models.itinerary import OfflineMutation, Stop
from app.services.permissions import require_edit_trip
from app.services.serialization import apply_fields


def enqueue_mutation(
    session: Session,
    *,
    trip_id: uuid.UUID,
    idempotency_key: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    operation: str,
    payload: dict,
    base_version: int | None,
    user_id: uuid.UUID | None,
) -> OfflineMutation:
    """Queue a mutation made offline. Idempotency key prevents double-apply."""
    existing = session.execute(
        select(OfflineMutation).where(OfflineMutation.idempotency_key == idempotency_key)
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    m = OfflineMutation(
        trip_id=trip_id,
        idempotency_key=idempotency_key,
        entity_type=entity_type,
        entity_id=entity_id,
        operation=operation,
        payload_json=payload,
        base_version=base_version,
        status="pending",
        created_by=user_id,
    )
    session.add(m)
    session.flush()
    return m


def process_mutation(session: Session, mutation: OfflineMutation, user) -> OfflineMutation:
    """Apply one queued mutation with optimistic-concurrency conflict detection.

    Returns the mutation with status 'applied' or 'conflict'. Never last-write-wins
    on a version mismatch; conflicts are reported for human resolution.
    """
    trip = session.get(Trip, mutation.trip_id)
    try:
        require_edit_trip(session, trip, user.id)
    except Exception:
        mutation.status = "conflict"
        mutation.error = "permission_denied"
        return mutation

    if mutation.entity_type == "stop" and mutation.entity_id:
        stop = session.get(Stop, mutation.entity_id)
        if stop is None:
            mutation.status = "conflict"
            mutation.error = "entity_not_found"
            return mutation
        if mutation.base_version is not None and stop.sequence_version != mutation.base_version:
            mutation.status = "conflict"
            mutation.error = (
                f"version_mismatch:client={mutation.base_version},server={stop.sequence_version}"
            )
            return mutation
        apply_fields(stop, mutation.payload_json)
        stop.sequence_version += 1
        mutation.status = "applied"
        return mutation

    mutation.status = "conflict"
    mutation.error = "unsupported_entity_type"
    return mutation


def process_outbox(session: Session, trip_id: uuid.UUID, user) -> list[OfflineMutation]:
    pending = session.execute(
        select(OfflineMutation)
        .where(OfflineMutation.trip_id == trip_id, OfflineMutation.status == "pending")
        .order_by(OfflineMutation.created_at)
    ).scalars().all()
    results = [process_mutation(session, m, user) for m in pending]
    session.flush()
    return results
