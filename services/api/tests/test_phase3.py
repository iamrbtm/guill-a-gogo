from app.seed.tennessee import seed_tennessee
from app.services.planner import (
    DayPlan,
    PlanConfig,
    PlanResult,
    StopMeta,
    plan_trip,
)
from app.services.providers.routing import (
    GoogleRoutingProvider,
    MockRoutingProvider,
    ProviderUnavailable,
)

TN_WAYPOINTS = [
    "Dallas, Oregon", "Redding, California", "Exeter, California",
    "Goodsprings, Nevada", "Las Vegas, Nevada", "Grand Canyon, Arizona",
    "Shawnee, Oklahoma", "Beggs, Oklahoma", "Little Rock, Arkansas",
    "Clarksville, Tennessee",
]


def _route():
    return MockRoutingProvider().route(TN_WAYPOINTS)


def test_planner_daily_division_and_breaks():
    route = _route()
    stops = [StopMeta(name=w, place=w, required=(w in TN_WAYPOINTS)) for w in TN_WAYPOINTS[1:]]
    config = PlanConfig(tank_gallons=30, towing_mpg=18.0, fuel_price_per_gallon=3.5)
    result = plan_trip(route, stops, config)

    assert isinstance(result, PlanResult)
    assert result.total_distance_mi == route.total_distance_mi
    # 9 legs ~ 3140 mi @ 60mph ~ 52h; at 8h/day -> ~7 days
    assert 5 <= len(result.days) <= 9
    # breaks occur roughly every 2h of driving
    for d in result.days:
        assert d.break_count == int(d.driving_hours // 2.0)
    # fuel computed where towing data present
    total_fuel = sum(d.fuel_gallons or 0 for d in result.days)
    assert total_fuel > 0
    # route provenance recorded
    assert result.route_source == "mock"
    assert result.route_status == "estimated"


def test_planner_single_leg_overflow_warns():
    # A single leg longer than the daily limit is unavoidable -> warning, no split.
    from app.services.providers.routing import RouteLeg, RouteResult

    leg = RouteLeg(from_place="A", to_place="B", distance_mi=1200, duration_seconds=72000)
    route = RouteResult(legs=[leg], total_distance_mi=1200, total_duration_seconds=72000)
    config = PlanConfig(max_daily_driving_hours=8.0, avg_speed_mph=60.0)
    result = plan_trip(route, [StopMeta(name="B", place="B")], config)

    overflow = [d for d in result.days if d.driving_hours > config.max_daily_driving_hours]
    assert overflow, "expected a day exceeding the max"
    assert any("exceeds max" in w for w in result.warnings)


def test_planner_respects_target_splitting():
    # Two normal legs should be split across days rather than overflowing.
    from app.services.providers.routing import RouteLeg, RouteResult

    legs = [
        RouteLeg(from_place="A", to_place="B", distance_mi=300, duration_seconds=18000),
        RouteLeg(from_place="B", to_place="C", distance_mi=300, duration_seconds=18000),
    ]
    route = RouteResult(legs=legs, total_distance_mi=600, total_duration_seconds=36000)
    config = PlanConfig(max_daily_driving_hours=8.0, avg_speed_mph=60.0)
    result = plan_trip(route, [StopMeta(name="B", place="B"), StopMeta(name="C", place="C")], config)
    assert all(d.driving_hours <= config.max_daily_driving_hours for d in result.days)


def test_provider_unavailable_degrades():
    # Unknown pair -> must raise, never invent a distance.
    try:
        MockRoutingProvider().route(["Nowhere", "Also Nowhere"])
        assert False, "should have raised"
    except ProviderUnavailable:
        pass
    # Google without a key must not fabricate.
    try:
        GoogleRoutingProvider(api_key=None).route(TN_WAYPOINTS)
        assert False, "should have raised"
    except ProviderUnavailable:
        pass


def test_tennessee_seed_fixture(make_user, db_session):
    owner = make_user("seed-owner@example.com")
    db_session.commit()
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    assert trip.origin == "Dallas, Oregon"
    assert trip.destination == "Clarksville, Tennessee"

    # 8 required/optional stops seeded.
    from app.models.itinerary import Stop
    stops = db_session.query(Stop).filter_by(trip_id=trip.id).all()
    assert len(stops) == 8
    assert any(s.name == "Redding, California" and s.required for s in stops)

    # Blocking warning present because the vehicle is intentionally incomplete.
    from app.models.itinerary import PlanningWarning
    warns = db_session.query(PlanningWarning).filter_by(trip_id=trip.id).all()
    assert any(w.severity == "blocking" for w in warns)
    assert any("Vehicle profile is incomplete" in w.message for w in warns)


def test_plan_endpoint_uses_mock_when_allowed(make_user, db_session, client, auth_header):
    import os
    from app.seed.tennessee import seed_tennessee

    os.environ["ALLOW_MOCK_PLANNING"] = "1"
    owner = make_user("plan-owner@example.com")
    db_session.commit()
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    resp = client.post(f"/api/v1/trips/{trip.id}/plan", headers=auth_header(owner), json={})
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["route_source"] == "mock"
    assert body["total_distance_mi"] > 0
    assert len(body["days"]) >= 1
    # Stops are required waypoints; days reflect deterministic division.
    os.environ.pop("ALLOW_MOCK_PLANNING", None)
