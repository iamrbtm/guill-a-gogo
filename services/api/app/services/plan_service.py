from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.itinerary import (
    Expense,
    LodgingCandidate,
    MealPlan,
    Reservation,
    Stop,
    TripDay,
)
from app.services import serialization
from app.services.permissions import require_edit_trip, require_view_trip
from app.services.trip_service import get_trip


def _edit(session, user, trip_id):
    trip = get_trip(session, user, trip_id)
    require_edit_trip(session, trip, user.id)
    return trip


def _view(session, user, trip_id):
    trip = get_trip(session, user, trip_id)
    require_view_trip(session, trip, user.id)
    return trip


# --- Trip days ---
def create_trip_day(session: Session, user, trip_id: uuid.UUID, data: dict) -> TripDay:
    _edit(session, user, trip_id)
    day = TripDay(trip_id=trip_id)
    serialization.apply_fields(day, data)
    session.add(day)
    session.flush()
    return day


def list_trip_days(session: Session, user, trip_id: uuid.UUID) -> list[TripDay]:
    _view(session, user, trip_id)
    return session.execute(
        select(TripDay).where(TripDay.trip_id == trip_id).order_by(TripDay.day_number)
    ).scalars().all()


def update_trip_day(session: Session, user, trip_id: uuid.UUID, day_id: uuid.UUID, data: dict) -> TripDay | None:
    _edit(session, user, trip_id)
    day = session.get(TripDay, day_id)
    if day is None or day.trip_id != trip_id:
        return None
    serialization.apply_fields(day, data)
    day.version += 1
    session.flush()
    return day


# --- Stops ---
def create_stop(session: Session, user, trip_id: uuid.UUID, data: dict) -> Stop:
    _edit(session, user, trip_id)
    stop = Stop(trip_id=trip_id)
    serialization.apply_fields(stop, data)
    session.add(stop)
    session.flush()
    return stop


def list_stops(session: Session, user, trip_id: uuid.UUID) -> list[Stop]:
    _view(session, user, trip_id)
    return session.execute(
        select(Stop).where(Stop.trip_id == trip_id).order_by(Stop.order_index)
    ).scalars().all()


def update_stop(session: Session, user, trip_id: uuid.UUID, stop_id: uuid.UUID, data: dict) -> Stop | None:
    _edit(session, user, trip_id)
    stop = session.get(Stop, stop_id)
    if stop is None or stop.trip_id != trip_id:
        return None
    serialization.apply_fields(stop, data)
    stop.sequence_version += 1
    session.flush()
    return stop


# --- Lodging ---
def create_lodging(session: Session, user, trip_id: uuid.UUID, data: dict) -> LodgingCandidate:
    _edit(session, user, trip_id)
    lodg = LodgingCandidate(trip_id=trip_id)
    serialization.apply_fields(lodg, data)
    session.add(lodg)
    session.flush()
    return lodg


def list_lodging(session: Session, user, trip_id: uuid.UUID) -> list[LodgingCandidate]:
    _view(session, user, trip_id)
    return session.execute(select(LodgingCandidate).where(LodgingCandidate.trip_id == trip_id)).scalars().all()


def confirm_lodging(
    session: Session, user, trip_id: uuid.UUID, lodging_id: uuid.UUID, confirmation: dict
) -> LodgingCandidate | None:
    """Mark a lodging candidate as human-confirmed and record a reservation.

    Never sets the accessibility/two-dog confirmation flags automatically; the
    caller supplies them explicitly (they reflect a human phone confirmation).
    """
    _edit(session, user, trip_id)
    lodg = session.get(LodgingCandidate, lodging_id)
    if lodg is None or lodg.trip_id != trip_id:
        return None
    lodg.user_confirmed = True
    lodg.confirmation_number = confirmation.get("confirmation_number")
    lodg.who_confirmed = confirmation.get("who_confirmed", user.email)
    lodg.confirmation_date = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    # Only the explicitly-provided confirmation booleans are accepted.
    for f in (
        "two_dogs_permitted", "weight_breed_restrictions_known", "pet_fees_in_total",
        "accessible_room_listed", "required_accessibility_confirmed", "breakfast_included",
        "trailer_parking_confirmed",
    ):
        if f in confirmation:
            setattr(lodg, f, bool(confirmation[f]))
    session.flush()
    res = Reservation(
        trip_id=trip_id,
        lodging_candidate_id=lodg.id,
        confirmation_number=lodg.confirmation_number,
        provider=confirmation.get("provider"),
        booker_user_id=user.id,
        notes=confirmation.get("notes"),
        source_link=confirmation.get("source_link"),
    )
    session.add(res)
    session.flush()
    return lodg


# --- Meals ---
def create_meal(session: Session, user, trip_id: uuid.UUID, data: dict) -> MealPlan:
    _edit(session, user, trip_id)
    meal = MealPlan(trip_id=trip_id)
    serialization.apply_fields(meal, data)
    session.add(meal)
    session.flush()
    return meal


def list_meals(session: Session, user, trip_id: uuid.UUID) -> list[MealPlan]:
    _view(session, user, trip_id)
    return session.execute(select(MealPlan).where(MealPlan.trip_id == trip_id)).scalars().all()


# --- Reservations ---
def create_reservation(session: Session, user, trip_id: uuid.UUID, data: dict) -> Reservation:
    _edit(session, user, trip_id)
    res = Reservation(trip_id=trip_id, booker_user_id=user.id)
    serialization.apply_fields(res, data)
    session.add(res)
    session.flush()
    return res


def list_reservations(session: Session, user, trip_id: uuid.UUID) -> list[Reservation]:
    _view(session, user, trip_id)
    return session.execute(select(Reservation).where(Reservation.trip_id == trip_id)).scalars().all()
