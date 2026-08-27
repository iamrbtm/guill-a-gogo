from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounts import Trip
from app.models.itinerary import Expense, PlanningWarning
from app.models.profiles import Vehicle
from app.services import serialization
from app.services.permissions import require_edit_trip, require_view_trip
from app.services.trip_service import get_trip
from app.services.vehicle_check import evaluate_trailer, evaluate_vehicle


def add_expense(session: Session, user, trip_id: uuid.UUID, data: dict) -> Expense:
    trip = get_trip(session, user, trip_id)
    # Any trip member may record an expense; owner/editor may modify later.
    from app.services.permissions import require_view_trip as _rv

    _rv(session, trip, user.id)
    exp = Expense(trip_id=trip_id, created_by=user.id)
    serialization.apply_fields(exp, data)
    session.add(exp)
    session.flush()
    return exp


def list_expenses(session: Session, user, trip_id: uuid.UUID) -> list[Expense]:
    trip = get_trip(session, user, trip_id)
    require_view_trip(session, trip, user.id)
    return session.execute(select(Expense).where(Expense.trip_id == trip_id)).scalars().all()


def refresh_trip_warnings(session: Session, user, trip_id: uuid.UUID) -> list[PlanningWarning]:
    """Recompute deterministic planning warnings for a trip (vehicle/trailer)."""
    trip = get_trip(session, user, trip_id)
    require_edit_trip(session, trip, user.id)
    session.execute(select(PlanningWarning).where(PlanningWarning.trip_id == trip_id)).scalars().all()
    for w in session.query(PlanningWarning).filter_by(trip_id=trip_id).all():
        session.delete(w)
    warnings: list[PlanningWarning] = []
    if trip.vehicle_id:
        veh = session.get(Vehicle, trip.vehicle_id)
        if veh:
            trailer = _trailer_of(session, trip)
            trailer_warnings = evaluate_trailer(trailer) if trailer else []
            for w in evaluate_vehicle(veh) + trailer_warnings:
                warnings.append(PlanningWarning(trip_id=trip_id, **w))
    session.add_all(warnings)
    session.flush()
    return warnings


def _trailer_of(session, trip):
    from app.models.profiles import Trailer

    return session.get(Trailer, trip.trailer_id) if trip.trailer_id else None


def list_warnings(session: Session, user, trip_id: uuid.UUID) -> list[PlanningWarning]:
    trip = get_trip(session, user, trip_id)
    require_view_trip(session, trip, user.id)
    return session.execute(select(PlanningWarning).where(PlanningWarning.trip_id == trip_id)).scalars().all()
