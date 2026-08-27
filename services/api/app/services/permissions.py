from __future__ import annotations

import uuid

from sqlalchemy.orm import Session
from werkzeug.exceptions import Forbidden, Unauthorized

from app.models.accounts import Trip, TripMembership

ROLE_OWNER = "owner"
ROLE_EDITOR = "editor"
ROLE_TRAVELER = "traveler"
ROLE_VIEWER = "viewer"

EDIT_ROLES = {ROLE_OWNER, ROLE_EDITOR}
VIEW_ROLES = {ROLE_OWNER, ROLE_EDITOR, ROLE_TRAVELER, ROLE_VIEWER}


def get_membership(session: Session, trip_id: uuid.UUID, user_id: uuid.UUID) -> TripMembership | None:
    return (
        session.query(TripMembership)
        .filter_by(trip_id=trip_id, user_id=user_id)
        .first()
    )


def trip_role(session: Session, trip: Trip, user_id: uuid.UUID) -> str | None:
    if trip.owner_id == user_id:
        return ROLE_OWNER
    m = get_membership(session, trip.id, user_id)
    return m.role if m else None


def require_trip_role(session: Session, trip: Trip, user_id: uuid.UUID, roles: set[str]) -> str:
    role = trip_role(session, trip, user_id)
    if role is None:
        raise Unauthorized("not_a_trip_member")
    if role not in roles:
        raise Forbidden("insufficient_trip_role")
    return role


def require_view_trip(session: Session, trip: Trip, user_id: uuid.UUID) -> str:
    return require_trip_role(session, trip, user_id, VIEW_ROLES)


def require_edit_trip(session: Session, trip: Trip, user_id: uuid.UUID) -> str:
    return require_trip_role(session, trip, user_id, EDIT_ROLES)


def require_manage_trip(session: Session, trip: Trip, user_id: uuid.UUID) -> str:
    return require_trip_role(session, trip, user_id, {ROLE_OWNER})


def profile_access_level(
    session: Session,
    *,
    profile_owner_id: uuid.UUID,
    user_id: uuid.UUID,
    linked_trip_ids: list[uuid.UUID],
) -> str:
    """Return 'write', 'read', or 'none' for a reusable profile.

    The profile owner may write. A trip owner/editor of any trip that links the
    profile may write. Any member of a linking trip may read.
    """
    if profile_owner_id == user_id:
        return "write"
    for trip_id in linked_trip_ids:
        trip = session.get(Trip, trip_id)
        if trip is None:
            continue
        role = trip_role(session, trip, user_id)
        if role in EDIT_ROLES:
            return "write"
        if role in VIEW_ROLES:
            return "read"
    return "none"


def require_profile_write(
    session: Session, *, profile_owner_id: uuid.UUID, user_id: uuid.UUID, linked_trip_ids: list[uuid.UUID]
) -> None:
    level = profile_access_level(
        session, profile_owner_id=profile_owner_id, user_id=user_id, linked_trip_ids=linked_trip_ids
    )
    if level != "write":
        raise Forbidden("profile_write_denied")


def require_profile_read(
    session: Session, *, profile_owner_id: uuid.UUID, user_id: uuid.UUID, linked_trip_ids: list[uuid.UUID]
) -> None:
    level = profile_access_level(
        session, profile_owner_id=profile_owner_id, user_id=user_id, linked_trip_ids=linked_trip_ids
    )
    if level == "none":
        raise Forbidden("profile_read_denied")
