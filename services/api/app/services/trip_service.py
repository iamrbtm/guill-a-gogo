from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounts import Trip, TripMembership, User, trip_pets, trip_travelers
from app.models.profiles import Pet, TravelerProfile, Vehicle
from app.services import serialization
from app.services.permissions import (
    require_edit_trip,
    require_manage_trip,
    require_view_trip,
)
from app.services.profile_service import _linked_trip_ids


def create_trip(session: Session, user, data: dict) -> Trip:
    trip = Trip(owner_id=user.id)
    serialization.apply_fields(trip, data)
    session.add(trip)
    session.flush()
    session.add(TripMembership(trip_id=trip.id, user_id=user.id, role="owner", invited_by=user.id))
    session.flush()
    return trip


def list_user_trips(session: Session, user) -> list[Trip]:
    owned = select(Trip).where(Trip.owner_id == user.id, Trip.deleted_at.is_(None))
    member_ids = select(TripMembership.trip_id).where(TripMembership.user_id == user.id)
    member = select(Trip).where(Trip.id.in_(member_ids), Trip.deleted_at.is_(None))
    seen = set()
    out = []
    for q in (owned, member):
        for t in session.execute(q).scalars().all():
            if t.id not in seen:
                seen.add(t.id)
                out.append(t)
    return out


def get_trip(session: Session, user, trip_id: uuid.UUID) -> Trip | None:
    trip = session.get(Trip, trip_id)
    if trip is None or trip.deleted_at is not None:
        return None
    require_view_trip(session, trip, user.id)
    return trip


def update_trip(session: Session, user, trip_id: uuid.UUID, data: dict) -> Trip | None:
    trip = session.get(Trip, trip_id)
    if trip is None or trip.deleted_at is not None:
        return None
    require_edit_trip(session, trip, user.id)
    serialization.apply_fields(trip, data)
    trip.version += 1
    session.flush()
    return trip


def add_member(session: Session, user, trip_id: uuid.UUID, target_user_id: uuid.UUID, role: str) -> TripMembership:
    trip = session.get(Trip, trip_id)
    if trip is None or trip.deleted_at is not None:
        raise ValueError("trip_not_found")
    require_manage_trip(session, trip, user.id)
    if role not in {"owner", "editor", "traveler", "viewer"}:
        raise ValueError("invalid_role")
    existing = session.query(TripMembership).filter_by(trip_id=trip_id, user_id=target_user_id).first()
    if existing:
        existing.role = role
        session.flush()
        return existing
    m = TripMembership(trip_id=trip_id, user_id=target_user_id, role=role, invited_by=user.id)
    session.add(m)
    session.flush()
    return m


def remove_member(session: Session, user, trip_id: uuid.UUID, target_user_id: uuid.UUID) -> bool:
    trip = session.get(Trip, trip_id)
    if trip is None:
        raise ValueError("trip_not_found")
    require_manage_trip(session, trip, user.id)
    m = session.query(TripMembership).filter_by(trip_id=trip_id, user_id=target_user_id).first()
    if m is None:
        return False
    if m.role == "owner":
        raise ValueError("cannot_remove_owner")
    session.delete(m)
    session.flush()
    return True


def _assert_vehicle_access(session: Session, user, vehicle_id: uuid.UUID) -> None:
    v = session.get(Vehicle, vehicle_id)
    if v is None:
        raise ValueError("vehicle_not_found")
    level = profile_access_level_vehicle(session, v, user.id)
    if level != "write":
        raise ValueError("vehicle_access_denied")


def profile_access_level_vehicle(session, vehicle, user_id):
    from app.services.permissions import profile_access_level

    return profile_access_level(
        session,
        profile_owner_id=vehicle.owner_id,
        user_id=user_id,
        linked_trip_ids=_linked_trip_ids(session, "vehicle", vehicle.id),
    )


def assign_vehicle(session: Session, user, trip_id: uuid.UUID, vehicle_id: uuid.UUID) -> Trip:
    trip = session.get(Trip, trip_id)
    if trip is None or trip.deleted_at is not None:
        raise ValueError("trip_not_found")
    require_edit_trip(session, trip, user.id)
    _assert_vehicle_access(session, user, vehicle_id)
    trip.vehicle_id = vehicle_id
    trip.version += 1
    session.flush()
    return trip


def assign_trailer(session: Session, user, trip_id: uuid.UUID, trailer_id: uuid.UUID) -> Trip:
    from app.models.profiles import Trailer

    trip = session.get(Trip, trip_id)
    if trip is None or trip.deleted_at is not None:
        raise ValueError("trip_not_found")
    require_edit_trip(session, trip, user.id)
    t = session.get(Trailer, trailer_id)
    if t is None:
        raise ValueError("trailer_not_found")
    trip.trailer_id = trailer_id
    trip.version += 1
    session.flush()
    return trip


def link_traveler(session: Session, user, trip_id: uuid.UUID, traveler_id: uuid.UUID) -> None:
    trip = get_trip(session, user, trip_id)
    require_edit_trip(session, trip, user.id)
    tp = session.get(TravelerProfile, traveler_id)
    if tp is None:
        raise ValueError("traveler_not_found")
    stmt = trip_travelers.insert().values(trip_id=trip_id, traveler_profile_id=traveler_id)
    session.execute(stmt)
    session.flush()


def unlink_traveler(session: Session, user, trip_id: uuid.UUID, traveler_id: uuid.UUID) -> None:
    trip = get_trip(session, user, trip_id)
    require_edit_trip(session, trip, user.id)
    session.execute(
        trip_travelers.delete().where(
            trip_travelers.c.trip_id == trip_id,
            trip_travelers.c.traveler_profile_id == traveler_id,
        )
    )
    session.flush()


def link_pet(session: Session, user, trip_id: uuid.UUID, pet_id: uuid.UUID) -> None:
    trip = get_trip(session, user, trip_id)
    require_edit_trip(session, trip, user.id)
    p = session.get(Pet, pet_id)
    if p is None:
        raise ValueError("pet_not_found")
    session.execute(trip_pets.insert().values(trip_id=trip_id, pet_id=pet_id))
    session.flush()
