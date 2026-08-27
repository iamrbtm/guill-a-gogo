import uuid

from app.models.accounts import Trip, TripMembership, User
from app.services import expense_service, profile_service
from app.services.permissions import trip_role
from app.services.vehicle_check import evaluate_vehicle
from app.models.profiles import Vehicle


def test_create_and_list_traveler_profile(client, make_user, auth_header, db_session):
    owner = make_user("owner-p2@example.com")
    h = auth_header(owner)
    resp = client.post(
        "/api/v1/profiles/traveler",
        headers=h,
        json={"name": "Mother", "max_walking_distance_meters": 30, "food_allergies": ["fish"]},
    )
    assert resp.status_code == 201, resp.get_json()
    pid = resp.get_json()["id"]

    lst = client.get("/api/v1/profiles/traveler", headers=h)
    assert lst.status_code == 200
    assert any(p["id"] == pid for p in lst.get_json())


def test_profile_isolation_between_users(client, make_user, auth_header, db_session):
    a = make_user("a@example.com")
    b = make_user("b@example.com")
    ha = auth_header(a)
    hb = auth_header(b)
    pid = client.post(
        "/api/v1/profiles/traveler", headers=ha, json={"name": "Secret"}
    ).get_json()["id"]
    # B cannot read A's private profile (not linked to any shared trip).
    assert client.get(f"/api/v1/profiles/traveler/{pid}", headers=hb).status_code == 403


def test_trip_crud_and_member_roles(client, make_user, auth_header, db_session):
    owner = make_user("owner2@example.com")
    editor = make_user("editor2@example.com")
    viewer = make_user("viewer2@example.com")
    ho = auth_header(owner)

    trip = client.post(
        "/api/v1/trips", headers=ho, json={"title": "TN Move", "origin": "Dallas, OR", "destination": "Clarksville, TN"}
    ).get_json()
    tid = trip["id"]

    # Owner adds members.
    client.post("/api/v1/trips/{}/members".format(tid), headers=ho, json={"user_id": str(editor.id), "role": "editor"})
    client.post("/api/v1/trips/{}/members".format(tid), headers=ho, json={"user_id": str(viewer.id), "role": "viewer"})

    # Viewer cannot edit.
    assert client.patch(
        "/api/v1/trips/{}".format(tid), headers=auth_header(viewer), json={"notes": "x"}
    ).status_code == 403

    # Editor can edit.
    edit = client.patch(
        "/api/v1/trips/{}".format(tid), headers=auth_header(editor), json={"notes": "edited by editor"}
    )
    assert edit.status_code == 200
    assert edit.get_json()["notes"] == "edited by editor"

    # Non-member is denied.
    stranger = make_user("stranger@example.com")
    assert client.get("/api/v1/trips/{}".format(tid), headers=auth_header(stranger)).status_code == 401


def test_vehicle_assignment_and_blocking_warning(client, make_user, auth_header, db_session):
    owner = make_user("owner3@example.com")
    ho = auth_header(owner)
    tid = client.post("/api/v1/trips", headers=ho, json={"title": "TN"}).get_json()["id"]

    # Incomplete vehicle (no year/make/model/etc.)
    vid = client.post(
        "/api/v1/profiles/vehicle", headers=ho, json={"make": "Volkswagen"}
    ).get_json()["id"]

    assign = client.post("/api/v1/trips/{}/vehicle".format(tid), headers=ho, json={"vehicle_id": vid})
    assert assign.status_code == 200

    warnings = client.post("/api/v1/trips/{}/warnings/refresh".format(tid), headers=ho).get_json()
    assert any(w["severity"] == "blocking" for w in warnings)
    assert warnings[0]["category"] == "vehicle_incomplete"


def test_vehicle_completeness_requires_real_values():
    v = Vehicle(make="VW")
    w = evaluate_vehicle(v)
    assert any(x["severity"] == "blocking" for x in w)
    # Complete + safe
    v2 = Vehicle(
        year=2005, make="Honda", model="Pilot", towing_mpg=18.0,
        rated_towing_capacity_kg=2000, loaded_trailer_weight_kg=1500, trim="EX",
    )
    assert evaluate_vehicle(v2) == []
    # Overload is blocking
    v3 = Vehicle(
        year=2005, make="Honda", model="Pilot", towing_mpg=18.0,
        rated_towing_capacity_kg=1500, loaded_trailer_weight_kg=2000, trim="EX",
    )
    assert any(x["category"] == "towing_overload" for x in evaluate_vehicle(v3))


def test_plan_stops_lodging_meals_reservations_expenses(client, make_user, auth_header, db_session):
    owner = make_user("owner4@example.com")
    ho = auth_header(owner)
    tid = client.post("/api/v1/trips", headers=ho, json={"title": "TN"}).get_json()["id"]

    stop = client.post(
        "/api/v1/trips/{}/stops".format(tid), headers=ho,
        json={"stop_type": "required_place", "name": "Redding, CA", "required": True, "order_index": 1},
    )
    assert stop.status_code == 201

    lodg = client.post(
        "/api/v1/trips/{}/lodging".format(tid), headers=ho,
        json={"name": "Hotel A", "pet_friendly_advertised": True},
    ).get_json()
    assert lodg["pet_friendly_advertised"] is True
    # Confirm with explicit human-verified accessibility flags (no auto-confirm).
    conf = client.post(
        "/api/v1/trips/{}/lodging/{}/confirm".format(tid, lodg["id"]), headers=ho,
        json={"confirmation_number": "ABC123", "who_confirmed": "Jeremy",
              "required_accessibility_confirmed": True, "two_dogs_permitted": True},
    )
    assert conf.status_code == 200
    assert conf.get_json()["user_confirmed"] is True
    assert conf.get_json()["required_accessibility_confirmed"] is True

    meal = client.post(
        "/api/v1/trips/{}/meals".format(tid), headers=ho,
        json={"meal_type": "dinner", "restaurant_name": "Cheddar's", "serves_fish": False},
    )
    assert meal.status_code == 201

    exp = client.post(
        "/api/v1/trips/{}/expenses".format(tid), headers=ho,
        json={"category": "fuel", "amount_minor": 4500, "currency": "USD"},
    )
    assert exp.status_code == 201
    assert exp.get_json()["amount_minor"] == 4500
