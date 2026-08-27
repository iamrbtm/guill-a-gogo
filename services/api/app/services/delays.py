from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy.orm import Session
from werkzeug.exceptions import Forbidden

from app.models.accounts import Trip
from app.models.itinerary import ChangeProposal, Reservation, Stop
from app.services.permissions import require_edit_trip


def propose_delay_revision(
    session: Session, trip: Trip, delay_minutes: int, user, *, now: dt.datetime | None = None
) -> ChangeProposal:
    """Create a pending revision when a delay pushes the remaining schedule.

    The stored itinerary is NOT changed here; an Owner/Editor must approve first.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    remaining = (
        session.query(Stop)
        .filter_by(trip_id=trip.id)
        .filter(Stop.completed.is_(False), Stop.skipped.is_(False))
        .order_by(Stop.order_index)
        .all()
    )

    before = [{"id": str(s.id), "order_index": s.order_index, "delay_minutes": 0} for s in remaining]
    after = [
        {"id": str(s.id), "order_index": s.order_index, "delay_minutes": delay_minutes}
        for s in remaining
    ]

    # Which reservations may be impacted (illustrative; no live check-in times).
    reservations = session.query(Reservation).filter_by(trip_id=trip.id).all()
    affected = [{"id": str(r.id), "confirmation_number": r.confirmation_number} for r in reservations]

    warnings = []
    if delay_minutes > 120:
        warnings.append("Delay exceeds 2h; confirm pet/restroom break spacing still meets ~2h cadence.")
    if affected:
        warnings.append(f"{len(affected)} reservation(s) may be impacted; verify check-in times before approving.")

    proposal = ChangeProposal(
        trip_id=trip.id,
        kind="delay_revision",
        title=f"Delay of {delay_minutes} min for remaining {len(remaining)} stop(s)",
        before={"stops": before},
        after={"stops": after, "applied_delay_minutes": delay_minutes},
        assumptions=["No reroute; arrival times shift uniformly by the delay.", "Fuel cost assumed unchanged."],
        warnings=warnings,
        status="pending",
        created_by=user.id,
    )
    session.add(proposal)
    session.flush()
    return proposal


def approve_proposal(session: Session, proposal_id: uuid.UUID, user) -> ChangeProposal:
    proposal = session.get(ChangeProposal, proposal_id)
    if proposal is None:
        raise ValueError("proposal_not_found")
    trip = session.get(Trip, proposal.trip_id)
    # Approval is an owner/editor action (schedule-changing).
    require_edit_trip(session, trip, user.id)
    if proposal.status != "pending":
        raise ValueError("proposal_not_pending")

    applied = proposal.after.get("applied_delay_minutes", 0)
    trip.applied_delay_minutes = (trip.applied_delay_minutes or 0) + applied
    trip.version += 1

    proposal.status = "approved"
    proposal.approved_by = user.id
    proposal.approved_at = dt.datetime.now(dt.timezone.utc)
    session.flush()
    return proposal


def reject_proposal(session: Session, proposal_id: uuid.UUID, user) -> ChangeProposal:
    proposal = session.get(ChangeProposal, proposal_id)
    if proposal is None:
        raise ValueError("proposal_not_found")
    trip = session.get(Trip, proposal.trip_id)
    require_edit_trip(session, trip, user.id)
    if proposal.status != "pending":
        raise ValueError("proposal_not_pending")
    proposal.status = "rejected"
    session.flush()
    return proposal
