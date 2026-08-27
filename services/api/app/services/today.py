from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.models.accounts import Trip
from app.models.itinerary import Reservation, Stop


def generate_nav_url(provider: str, origin: str, destination: str) -> str:
    """One-tap deep link to open the selected route leg in a maps app.

    Provider is chosen per profile; we never implement turn-by-turn navigation.
    """
    if provider == "google":
        return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=driving"
    if provider == "apple":
        return f"https://maps.apple.com/?daddr={destination}&saddr={origin}&dirflg=d"
    # Default to Google Maps web deep link.
    return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=driving"


def _current_day_number(trip: Trip, now: dt.datetime) -> int:
    if trip.start_date:
        start = trip.start_date
        if start.tzinfo is None:
            start = start.replace(tzinfo=dt.timezone.utc)
        delta = (now - start).days
        if delta >= 0:
            return delta + 1
    return 1


def build_today_dashboard(session: Session, trip: Trip, now: dt.datetime | None = None) -> dict:
    """Deterministic, low-clutter travel-day dashboard.

    Without a live routing/position provider this returns the planned schedule
    and clearly marks ETA/position data as requiring connectivity rather than
    inventing it.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    stops = (
        session.query(Stop).filter_by(trip_id=trip.id).order_by(Stop.order_index).all()
    )
    completed = [s for s in stops if s.completed]
    remaining = [s for s in stops if not s.completed and not s.skipped]
    next_stop = remaining[0] if remaining else None

    day_number = _current_day_number(trip, now)
    reservations = (
        session.query(Reservation).filter_by(trip_id=trip.id).all()
    )

    return {
        "trip_id": str(trip.id),
        "trip_title": trip.title,
        "day_number": day_number,
        "origin": trip.origin,
        "destination": trip.destination,
        "next_stop": (
            {
                "id": str(next_stop.id),
                "name": next_stop.name,
                "address": next_stop.address,
                "required": next_stop.required,
                "stop_type": next_stop.stop_type,
            }
            if next_stop
            else None
        ),
        "remaining_stops": [
            {"id": str(s.id), "name": s.name, "required": s.required, "stop_type": s.stop_type}
            for s in remaining
        ],
        "completed_count": len(completed),
        "remaining_count": len(remaining),
        "reservations": [
            {"id": str(r.id), "confirmation_number": r.confirmation_number, "provider": r.provider}
            for r in reservations
        ],
        "eta_note": "Live position and ETA require a routing provider; plan reflects scheduled stops.",
        "actions": {
            "can_depart": next_stop is not None,
            "can_arrive": next_stop is not None,
            "can_complete_stop": next_stop is not None,
            "can_delay": next_stop is not None,
            "can_skip": next_stop is not None,
            "can_emergency_pause": True,
        },
    }
