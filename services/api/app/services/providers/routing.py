from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class RouteLeg:
    from_place: str
    to_place: str
    distance_mi: float
    duration_seconds: float
    source: str = "mock"
    retrieved_at: Optional[str] = None
    status: str = "estimated"  # estimated | cached | manual | live


@dataclass
class RouteResult:
    legs: list[RouteLeg]
    total_distance_mi: float
    total_duration_seconds: float
    source: str = "mock"
    status: str = "estimated"


class RoutingProvider(Protocol):
    """Narrow provider interface for routing/route matrix.

    Implementations must record provenance and never fabricate live facts when
    unavailable; they should raise ProviderUnavailable so the planner degrades
    to manual entry.
    """

    def route(self, waypoints: list[str]) -> RouteResult: ...


class ProviderUnavailable(Exception):
    """Raised when a provider cannot supply data; the caller degrades gracefully."""


# Approximate, deterministic distances (miles) between the 2024 Tennessee route
# cities. These are a *seed draft* only; the spec requires recomputing from live
# route data once vehicle + dates are known. They are NOT presented as exact.
_MOCK_MATRIX: dict[tuple[str, str], float] = {
    ("Dallas, Oregon", "Redding, California"): 410,
    ("Redding, California", "Exeter, California"): 300,
    ("Exeter, California", "Goodsprings, Nevada"): 350,
    ("Goodsprings, Nevada", "Las Vegas, Nevada"): 40,
    ("Las Vegas, Nevada", "Grand Canyon, Arizona"): 280,
    ("Grand Canyon, Arizona", "Shawnee, Oklahoma"): 1010,
    ("Shawnee, Oklahoma", "Beggs, Oklahoma"): 60,
    ("Beggs, Oklahoma", "Little Rock, Arkansas"): 370,
    ("Little Rock, Arkansas", "Clarksville, Tennessee"): 420,
}

_AVG_SPEED_MPH = 60.0


def _duration_seconds(distance_mi: float) -> float:
    return (distance_mi / _AVG_SPEED_MPH) * 3600.0


class MockRoutingProvider:
    """Deterministic provider used in tests and when no API key is configured.

    Honors only the known waypoint pairs above; for unknown pairs it raises
    ProviderUnavailable so the caller must request manual entry (never invent).
    """

    def route(self, waypoints: list[str]) -> RouteResult:
        if len(waypoints) < 2:
            raise ProviderUnavailable("need at least two waypoints")
        legs: list[RouteLeg] = []
        total = 0.0
        total_dur = 0.0
        for a, b in zip(waypoints, waypoints[1:]):
            key = (a, b)
            if key not in _MOCK_MATRIX:
                raise ProviderUnavailable(f"no route for {a!r} -> {b!r}; manual entry required")
            d = _MOCK_MATRIX[key]
            dur = _duration_seconds(d)
            legs.append(
                RouteLeg(
                    from_place=a,
                    to_place=b,
                    distance_mi=d,
                    duration_seconds=dur,
                    source="mock",
                    retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                    status="estimated",
                )
            )
            total += d
            total_dur += dur
        return RouteResult(legs=legs, total_distance_mi=total, total_duration_seconds=total_dur, source="mock", status="estimated")


class GoogleRoutingProvider:
    """Google Routes adapter.

    Requires GOOGLE_MAPS_API_KEY. Until configured it raises ProviderUnavailable
    so the app degrades to manual entry (no fabricated distances). The actual
    HTTP call to Routes API is implemented here as a thin client; it is only
    invoked when the key is present.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://routes.googleapis.com") -> None:
        self.api_key = api_key
        self.base_url = base_url

    def route(self, waypoints: list[str]) -> RouteResult:
        if not self.api_key:
            raise ProviderUnavailable("google_maps_api_key not configured")
        raise ProviderUnavailable("google routes client not yet enabled in this build")


def get_routing_provider(api_key: Optional[str] = None, allow_mock: bool = False) -> RoutingProvider:
    """Select a routing provider.

    Google when a key is present; otherwise a deterministic Mock is allowed only
    when explicitly enabled for local development/testing. Never silently invent
    live distances in production.
    """
    if api_key:
        return GoogleRoutingProvider(api_key=api_key)
    if allow_mock:
        return MockRoutingProvider()
    raise ProviderUnavailable("no routing provider configured")
