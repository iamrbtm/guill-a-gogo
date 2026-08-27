from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounts import Trip, trip_pets, trip_travelers
from app.models.profiles import Pet, Preference, Trailer, TravelerProfile, Vehicle
from app.services import serialization
from app.services.current_user import resolve_current_user
from app.services.permissions import require_profile_read, require_profile_write

_PROFILE_MODELS = {
    "traveler": TravelerProfile,
    "pet": Pet,
    "vehicle": Vehicle,
    "trailer": Trailer,
    "preference": Preference,
}


def _linked_trip_ids(session: Session, kind: str, profile_id: uuid.UUID) -> list[uuid.UUID]:
    """Trips that reference this profile (drives profile sharing permissions)."""
    if kind == "traveler":
        rows = session.execute(
            select(trip_travelers.c.trip_id).where(trip_travelers.c.traveler_profile_id == profile_id)
        ).all()
        return [r[0] for r in rows]
    if kind == "pet":
        rows = session.execute(
            select(trip_pets.c.trip_id).where(trip_pets.c.pet_id == profile_id)
        ).all()
        return [r[0] for r in rows]
    if kind == "vehicle":
        rows = session.execute(select(Trip.id).where(Trip.vehicle_id == profile_id)).all()
        return [r[0] for r in rows]
    if kind == "trailer":
        rows = session.execute(select(Trip.id).where(Trip.trailer_id == profile_id)).all()
        return [r[0] for r in rows]
    return []


def create_profile(session: Session, user, kind: str, data: dict):
    model_cls = _PROFILE_MODELS[kind]
    obj = model_cls(owner_id=user.id)
    serialization.apply_fields(obj, data)
    session.add(obj)
    session.flush()
    return obj


def list_profiles(session: Session, user, kind: str) -> list:
    model_cls = _PROFILE_MODELS[kind]
    rows = session.execute(select(model_cls).where(model_cls.deleted_at.is_(None))).scalars().all()
    out = []
    for r in rows:
        linked = _linked_trip_ids(session, kind, r.id)
        level = _access_level(session, r.owner_id, user.id, linked)
        if level != "none":
            out.append(r)
    return out


def get_profile(session: Session, user, kind: str, profile_id: uuid.UUID):
    model_cls = _PROFILE_MODELS[kind]
    obj = session.get(model_cls, profile_id)
    if obj is None or obj.deleted_at is not None:
        return None
    linked = _linked_trip_ids(session, kind, obj.id)
    require_profile_read(session, profile_owner_id=obj.owner_id, user_id=user.id, linked_trip_ids=linked)
    return obj


def update_profile(session: Session, user, kind: str, profile_id: uuid.UUID, data: dict):
    obj = get_profile(session, user, kind, profile_id)
    if obj is None:
        return None
    linked = _linked_trip_ids(session, kind, obj.id)
    require_profile_write(session, profile_owner_id=obj.owner_id, user_id=user.id, linked_trip_ids=linked)
    serialization.apply_fields(obj, data)
    session.flush()
    return obj


def delete_profile(session: Session, user, kind: str, profile_id: uuid.UUID) -> bool:
    obj = get_profile(session, user, kind, profile_id)
    if obj is None:
        return False
    linked = _linked_trip_ids(session, kind, obj.id)
    require_profile_write(session, profile_owner_id=obj.owner_id, user_id=user.id, linked_trip_ids=linked)
    obj.deleted_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    session.flush()
    return True


def _access_level(session, owner_id, user_id, linked_trip_ids):
    from app.services.permissions import profile_access_level

    return profile_access_level(
        session, profile_owner_id=owner_id, user_id=user_id, linked_trip_ids=linked_trip_ids
    )
