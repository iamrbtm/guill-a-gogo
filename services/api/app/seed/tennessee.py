from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.accounts import Trip, TripMembership, trip_pets, trip_travelers
from app.models.itinerary import PlanningWarning, Stop
from app.models.profiles import Pet, Trailer, TravelerProfile, Vehicle
from app.services.expense_service import refresh_trip_warnings
from app.services.serialization import apply_fields

# Deterministic UUIDs so re-running the seed updates in place (repeatable).
_NS = uuid.uuid5(uuid.NAMESPACE_DNS, "guill-a-gogo.seed.tennessee")


def _id(name: str) -> uuid.UUID:
    return uuid.uuid5(_NS, name)


def _upsert(session: Session, model, pk: uuid.UUID, data: dict, owner_id=None, trip_id=None):
    obj = session.get(model, pk)
    if obj is None:
        obj = model(id=pk)
        session.add(obj)
    apply_fields(obj, data)
    cols = {c.name for c in obj.__table__.columns}
    if owner_id is not None and "owner_id" in cols:
        obj.owner_id = owner_id
    if trip_id is not None and "trip_id" in cols:
        obj.trip_id = trip_id
    session.flush()
    return obj


def seed_tennessee(session: Session, owner_user) -> Trip:
    """Import the initial Dallas, OR -> Clarksville, TN move as a repeatable fixture.

    Deliberately leaves dog weights/breeds and the vehicle facts incomplete so the
    app surfaces the required blocking warnings instead of guessing them.
    """
    owner_id = owner_user.id

    # --- Travelers (reusable profiles) ---
    mother = _upsert(
        session, TravelerProfile, _id("traveler:mother"), owner_id=owner_id, data={
            "name": "Mother",
            "max_walking_distance_meters": 30,  # ~100 ft
            "mobility_devices": ["collapsible wheelchair", "walker"],
            "transfer_needs": "Vehicle-to-wheelchair transfers; wheelchair and walker travel in trailer.",
            "accessible_restroom_needs": "Accessible restroom required",
            "routine_preferences": "Predictable timing reduces stress",
        },
    )
    jeremy = _upsert(
        session, TravelerProfile, _id("traveler:jeremy"), owner_id=owner_id, data={
            "name": "Jeremy",
            "max_walking_distance_meters": 90,  # ~football field
            "transfer_needs": "No toes on right foot; recovering from left tibia break.",
        },
    )
    nephew = _upsert(
        session, TravelerProfile, _id("traveler:nephew"), owner_id=owner_id, data={
            "name": "Nephew",
            "max_walking_distance_meters": 5000,
            "sensory_considerations": "Asperger's; benefits from predictable timing and low-surprise changes.",
        },
    )

    # --- Pets: two dogs; weights/breeds UNKNOWN -> required fields left blank ---
    dog1 = _upsert(
        session, Pet, _id("pet:dog1"), owner_id=owner_id, data={
            "name": "Dog 1 (unnamed)", "species": "dog", "break_frequency_minutes": 120,
            "hotel_restrictions": "Two dogs; breed/weight not yet known",
        },
    )
    dog2 = _upsert(
        session, Pet, _id("pet:dog2"), owner_id=owner_id, data={
            "name": "Dog 2 (unnamed)", "species": "dog", "break_frequency_minutes": 120,
            "hotel_restrictions": "Two dogs; breed/weight not yet known",
        },
    )

    # --- Vehicle: intentionally INCOMPLETE -> blocking warning ---
    vehicle = _upsert(
        session, Vehicle, _id("vehicle:move"), owner_id=owner_id, data={
            "make": "Volkswagen",  # year/model/trim/towing facts unknown
            "notes": "Do NOT guess year/make/model/fuel economy/towing capacity. Family to supply.",
        },
    )

    # --- Trailer: small; weights unknown ---
    trailer = _upsert(
        session, Trailer, _id("trailer:move"), owner_id=owner_id, data={
            "name": "Small trailer",
            "notes": "Carries luggage, collapsible wheelchair, and walker.",
        },
    )

    # --- Trip ---
    trip = _upsert(
        session, Trip, _id("trip:tennessee"), owner_id=owner_id, data={
            "title": "Dallas, OR → Clarksville, TN (Move)",
            "status": "draft",
            "origin": "Dallas, Oregon",
            "destination": "Clarksville, Tennessee",
            "timezone_policy": "America/Chicago",
            "notes": "Approx 11-day, 3,140-mi draft; recompute from live route once vehicle+dates known.",
            "vehicle_id": vehicle.id,
            "trailer_id": trailer.id,
        },
    )
    # Ensure owner membership.
    if session.query(TripMembership).filter_by(trip_id=trip.id, user_id=owner_id).first() is None:
        session.execute(
            TripMembership.__table__.insert().values(
                trip_id=trip.id, user_id=owner_id, role="owner", invited_by=owner_id
            )
        )
    # Link travelers + pets.
    for tp in (mother, jeremy, nephew):
        session.execute(trip_travelers.insert().values(trip_id=trip.id, traveler_profile_id=tp.id))
    for p in (dog1, dog2):
        session.execute(trip_pets.insert().values(trip_id=trip.id, pet_id=p.id))
    session.flush()

    # --- Required stops / visits ---
    required = [
        ("Redding, California", True, 120, "Bethel Church + prayer room; allow at least two hours."),
        ("Exeter, California", True, 2880, "Family visit; stay two nights. Lodging may be Tulare if Exeter lacks pet+accessibility."),
        ("Goodsprings, Nevada", False, 30, "Short stop at the bar tied to nephew's game interest."),
        ("Las Vegas, Nevada", True, 1440, "One overnight for nephew's delayed 21st-birthday trip."),
        ("Grand Canyon, Arizona", True, 2880, "Accessible visit; two-night assumption (editable)."),
        ("Shawnee, Oklahoma", False, 60, "Meal with friends."),
        ("Beggs, Oklahoma", False, 60, "Meal with friends."),
        ("Little Rock, Arkansas", True, 1440, "Overnight if needed to keep OK→TN within daily driving limits."),
    ]
    order = 1
    for place, is_req, min_dur, notes in required:
        _upsert(
            session, Stop, _id(f"stop:{place}"), trip_id=trip.id, data={
    
            "trip_id": trip.id,
                "order_index": order,
                "required": is_req,
                "stop_type": "required_place",
                "name": place,
                "address": place,
                "min_duration_minutes": min_dur,
                "notes": notes,
            },
        )
        order += 1
    session.flush()

    # Recompute deterministic warnings (vehicle incomplete -> blocking).
    refresh_trip_warnings(session, owner_user, trip.id)
    session.flush()
    return trip
