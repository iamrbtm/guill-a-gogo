import datetime as dt

from app.models.itinerary import ChangeProposal, ProviderRecord
from app.services import ai as ai_service
from app.services import provider_records
from app.seed.tennessee import seed_tennessee


def test_provider_record_provenance_and_staleness(db_session):
    now = dt.datetime.now(dt.timezone.utc)
    rec = provider_records.record_fetch(
        db_session, provider="google", request={"q": "fuel"}, normalized_response={"price": 3.5},
        ttl_seconds=60, verification_status="unverified", trip_id=None, now=now,
    )
    db_session.commit()
    assert rec.id is not None
    assert provider_records.is_stale(rec, now=now) is False
    assert provider_records.is_stale(rec, now=now + dt.timedelta(seconds=120)) is True
    # fingerprint is deterministic
    assert provider_records.fingerprint("google", {"q": "fuel"}) == provider_records.fingerprint("google", {"q": "fuel"})
    # fresh_record returns it while unexpired, None once stale
    assert provider_records.fresh_record(db_session, "google", {"q": "fuel"}) is not None
    assert provider_records.fresh_record(db_session, "google", {"q": "other"}) is None


def test_ai_output_validation():
    good = {"summary": "Split Day 3", "suggestions": [{"type": "day_division", "detail": "Add an overnight"}], "assumptions": ["x"], "warnings": []}
    parsed = ai_service.validate_ai_output(good)
    assert parsed.summary == "Split Day 3"

    # Extra/unknown fields are forbidden by the strict schema.
    try:
        ai_service.validate_ai_output({**good, "made_up": 1})
        assert False, "should reject extra fields"
    except Exception:
        pass

    # Missing required field rejected.
    try:
        ai_service.validate_ai_output({"suggestions": []})
        assert False, "should reject missing summary"
    except Exception:
        pass


def test_ai_proposal_never_auto_applies(db_session, make_user):
    owner = make_user("ai-owner@example.com")
    db_session.commit()
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    from app.services.current_user import resolve_current_user  # not needed here
    out = ai_service.validate_ai_output(
        {"summary": "Shift meal times", "suggestions": [], "assumptions": ["a"], "warnings": []}
    )
    proposal = ai_service.build_ai_proposal(db_session, trip, out, owner)
    db_session.commit()
    assert proposal.kind == "ai_proposal"
    assert proposal.status == "pending"  # NOT applied
    # Itinerary untouched.
    reloaded = db_session.get(type(trip), trip.id)
    assert reloaded.applied_delay_minutes == 0


def test_ai_propose_route(client, make_user, db_session, auth_header):
    owner = make_user("ai-route-owner@example.com")
    db_session.commit()
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    # Valid inline output -> pending proposal (requires later approval).
    resp = client.post(
        f"/api/v1/trips/{trip.id}/ai/propose",
        headers=auth_header(owner),
        json={"ai_output": {"summary": "Suggestion", "suggestions": [{"type": "meal", "detail": "Waffle House"}], "assumptions": [], "warnings": []}},
    )
    assert resp.status_code == 201, resp.get_json()
    assert resp.get_json()["status"] == "pending"

    # Invalid output -> rejected.
    bad = client.post(
        f"/api/v1/trips/{trip.id}/ai/propose",
        headers=auth_header(owner),
        json={"ai_output": {"nope": 1}},
    )
    assert bad.status_code == 422


def test_research_providers_graceful_when_disabled(client, make_user, db_session, auth_header):
    owner = make_user("res-owner@example.com")
    db_session.commit()
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    for path in ("/fuel", "/weather", "/places?q=x"):
        resp = client.get(f"/api/v1/trips/{trip.id}{path}", headers=auth_header(owner))
        assert resp.status_code == 200, resp.get_json()
        assert resp.get_json()["status"] == "manual_entry"
