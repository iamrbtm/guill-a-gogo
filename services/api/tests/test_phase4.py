import uuid

from app.seed.tennessee import seed_tennessee
from app.services.today import generate_nav_url


def test_nav_deep_links():
    g = generate_nav_url("google", "Dallas, OR", "Redding, CA")
    assert "google.com/maps/dir" in g and "Dallas" in g
    a = generate_nav_url("apple", "Dallas, OR", "Redding, CA")
    assert "maps.apple.com" in a


def test_today_dashboard_seeded(client, make_user, db_session, auth_header):
    owner = make_user("today-owner@example.com")
    db_session.commit()
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    resp = client.get(f"/api/v1/trips/{trip.id}/today", headers=auth_header(owner))
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["remaining_count"] == 8
    assert body["next_stop"]["name"] == "Redding, California"
    assert body["actions"]["can_emergency_pause"] is True


def test_delay_creates_proposal_and_approve_applies(client, make_user, db_session, auth_header):
    owner = make_user("delay-owner@example.com")
    db_session.commit()
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    prop = client.post(
        f"/api/v1/trips/{trip.id}/delays", headers=auth_header(owner),
        json={"delay_minutes": 90},
    )
    assert prop.status_code == 201, prop.get_json()
    pid = prop.get_json()["id"]

    # Before approval, trip delay is 0.
    assert client.get(f"/api/v1/trips/{trip.id}", headers=auth_header(owner)).get_json()["applied_delay_minutes"] == 0

    approved = client.post(
        f"/api/v1/trips/{trip.id}/proposals/{pid}/approve", headers=auth_header(owner)
    )
    assert approved.status_code == 200
    assert approved.get_json()["status"] == "approved"
    # After approval, the delay is applied to the trip.
    assert client.get(f"/api/v1/trips/{trip.id}", headers=auth_header(owner)).get_json()["applied_delay_minutes"] == 90


def test_sync_applies_and_detects_conflict(client, make_user, db_session, auth_header):
    owner = make_user("sync-owner@example.com")
    db_session.commit()
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    # Pick a stop and build an offline mutation against its current version.
    from app.models.itinerary import Stop
    stop = db_session.query(Stop).filter_by(trip_id=trip.id).order_by(Stop.order_index).first()
    base_version = stop.sequence_version
    key = "idem-123"

    payload = {"notes": "Updated via offline outbox"}
    mut = {
        "idempotency_key": key,
        "entity_type": "stop",
        "entity_id": str(stop.id),
        "operation": "update",
        "payload": payload,
        "base_version": base_version,
    }
    res = client.post(f"/api/v1/trips/{trip.id}/sync", headers=auth_header(owner), json={"mutations": [mut]})
    assert res.status_code == 200, res.get_json()
    processed = res.get_json()["processed"]
    assert processed[0]["status"] == "applied"

    # Idempotency: re-sending the same key yields the same applied record, no double apply.
    res2 = client.post(f"/api/v1/trips/{trip.id}/sync", headers=auth_header(owner), json={"mutations": [mut]})
    assert res2.get_json()["processed"][0]["status"] == "applied"

    # Conflict: a mutation with a stale base_version must NOT silently overwrite.
    stale = dict(mut, idempotency_key="idem-456", base_version=base_version)
    # bump server version first
    stop.sequence_version += 1
    db_session.commit()
    res3 = client.post(f"/api/v1/trips/{trip.id}/sync", headers=auth_header(owner), json={"mutations": [stale]})
    assert res3.get_json()["processed"][0]["status"] == "conflict"
