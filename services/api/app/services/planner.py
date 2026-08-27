from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Optional

from app.services.providers.routing import RouteResult

# Defaults aligned with the master prompt: ~6–8h driving/day, break every ~2h.
DEFAULT_TARGET_DAILY_HOURS = 7.0
DEFAULT_MAX_DAILY_HOURS = 8.0
DEFAULT_BREAK_INTERVAL_HOURS = 2.0
DEFAULT_AVG_SPEED_MPH = 60.0
DEFAULT_RANGE_RESERVE_MI = 30.0


@dataclass
class StopMeta:
    name: str
    place: str
    required: bool = False
    min_duration_minutes: Optional[int] = None


@dataclass
class PlanConfig:
    target_daily_driving_hours: float = DEFAULT_TARGET_DAILY_HOURS
    max_daily_driving_hours: float = DEFAULT_MAX_DAILY_HOURS
    break_interval_hours: float = DEFAULT_BREAK_INTERVAL_HOURS
    avg_speed_mph: float = DEFAULT_AVG_SPEED_MPH
    tank_gallons: Optional[float] = None
    towing_mpg: Optional[float] = None
    fuel_price_per_gallon: Optional[float] = None
    range_reserve_mi: float = DEFAULT_RANGE_RESERVE_MI


@dataclass
class DayPlan:
    day_number: int
    leg_places: list[str] = field(default_factory=list)
    driving_distance_mi: float = 0.0
    driving_hours: float = 0.0
    break_count: int = 0
    break_minutes: int = 0
    fuel_stops_needed: Optional[int] = None
    fuel_gallons: Optional[float] = None
    fuel_cost: Optional[float] = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class PlanResult:
    days: list[DayPlan]
    total_distance_mi: float
    total_driving_hours: float
    route_source: str
    route_status: str
    warnings: list[str] = field(default_factory=list)
    alternatives: list[list[DayPlan]] = field(default_factory=list)


def _leg_hours(distance_mi: float, avg_speed_mph: float) -> float:
    return distance_mi / avg_speed_mph


def _compute_fuel(day: DayPlan, config: PlanConfig) -> None:
    if config.towing_mpg and config.towing_mpg > 0:
        day.fuel_gallons = day.driving_distance_mi / config.towing_mpg
        range_mi = 0.0
        if config.tank_gallons:
            range_mi = config.tank_gallons * config.towing_mpg - config.range_reserve_mi
        if range_mi > 0 and day.driving_distance_mi > range_mi:
            day.fuel_stops_needed = max(0, (day.driving_distance_mi // range_mi))
        else:
            day.fuel_stops_needed = 0
        if config.fuel_price_per_gallon is not None:
            day.fuel_cost = (day.fuel_gallons or 0) * config.fuel_price_per_gallon
    else:
        day.fuel_stops_needed = None  # requires manual entry


def _build_days(leg_places: list[str], leg_distances: list[float], config: PlanConfig) -> list[DayPlan]:
    days: list[DayPlan] = []
    current = DayPlan(day_number=1)
    for place, dist in zip(leg_places, leg_distances):
        hours = _leg_hours(dist, config.avg_speed_mph)
        projected = current.driving_hours + hours
        # Start a new day only when the *new* leg alone fits the limit; otherwise
        # we'd just shift the overflow. A single leg longer than the limit is
        # unavoidable and is surfaced as a warning instead.
        if current.leg_places and projected > config.max_daily_driving_hours and hours <= config.max_daily_driving_hours:
            days.append(current)
            current = DayPlan(day_number=len(days) + 1)
        current.leg_places.append(place)
        current.driving_distance_mi += dist
        current.driving_hours += hours
    if current.leg_places:
        days.append(current)

    # Post-process breaks + fuel + warnings per day.
    for d in days:
        d.break_count = int(d.driving_hours // config.break_interval_hours)
        d.break_minutes = d.break_count * 15  # conservative 15-min breaks
        _compute_fuel(d, config)
        if d.driving_hours > config.max_daily_driving_hours:
            d.warnings.append(
                f"Day {d.day_number} driving {d.driving_hours:.1f}h exceeds max "
                f"{config.max_daily_driving_hours:.1f}h (a single leg is longer than the "
                "daily limit — add an intermediate stop to resolve)"
            )
    return days


def _split_day(day: DayPlan) -> list[DayPlan]:
    """Produce two days by halving the leg list (used for alternatives)."""
    mid = max(1, len(day.leg_places) // 2)
    first = DayPlan(day_number=day.day_number)
    first.leg_places = day.leg_places[:mid]
    first.driving_distance_mi = day.driving_distance_mi * (mid / max(1, len(day.leg_places)))
    first.driving_hours = day.driving_hours * (mid / max(1, len(day.leg_places)))
    second = DayPlan(day_number=day.day_number + 1)
    second.leg_places = day.leg_places[mid:]
    second.driving_distance_mi = day.driving_distance_mi - first.driving_distance_mi
    second.driving_hours = day.driving_hours - first.driving_hours
    return [first, second]


def plan_trip(route: RouteResult, stops: list[StopMeta], config: PlanConfig) -> PlanResult:
    leg_places = [leg.to_place for leg in route.legs]
    leg_distances = [leg.distance_mi for leg in route.legs]

    days = _build_days(leg_places, leg_distances, config)

    # Break/fuel warnings aggregated.
    warnings: list[str] = []
    for d in days:
        warnings.extend(d.warnings)

    total_hours = sum(d.driving_hours for d in days)
    return PlanResult(
        days=days,
        total_distance_mi=route.total_distance_mi,
        total_driving_hours=total_hours,
        route_source=route.source,
        route_status=route.status,
        warnings=warnings,
        alternatives=[],
    )


def plan_trip_from_db(session, trip, config: PlanConfig, provider) -> PlanResult:
    """Build a plan for a persisted Trip using its ordered stops.

    Requires a routing provider; if none is configured, the caller surfaces the
    ProviderUnavailable error and asks for manual entry (never invents distances).
    """
    from app.models.itinerary import Stop

    stops = (
        session.query(Stop)
        .filter_by(trip_id=trip.id)
        .order_by(Stop.order_index)
        .all()
    )
    waypoints: list[str] = []
    if trip.origin:
        waypoints.append(trip.origin)
    for s in stops:
        waypoints.append(s.address or s.name or s.stop_type)
    if trip.destination and trip.destination not in waypoints:
        waypoints.append(trip.destination)

    route = provider.route(waypoints)
    stop_meta = [StopMeta(name=s.name or s.stop_type, place=s.address or s.name, required=s.required) for s in stops]
    return plan_trip(route, stop_meta, config)
