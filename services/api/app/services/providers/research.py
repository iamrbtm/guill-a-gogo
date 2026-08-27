from __future__ import annotations

from app.config import get_settings
from app.services.providers.routing import ProviderUnavailable


def get_fuel_price(*, location: str | None = None):
    """Fuel price lookup. Requires a configured provider; otherwise callers must
    ask for manual entry and never present an assumed price as live."""
    if not get_settings().google_maps_api_key:
        raise ProviderUnavailable("fuel provider not configured")
    raise ProviderUnavailable("fuel provider client not enabled in this build")


def get_weather(*, location: str | None = None):
    if not get_settings().google_maps_api_key:
        raise ProviderUnavailable("weather provider not configured")
    raise ProviderUnavailable("weather provider client not enabled in this build")


def search_places(*, query: str, location: str | None = None):
    if not get_settings().google_maps_api_key:
        raise ProviderUnavailable("places provider not configured")
    raise ProviderUnavailable("places provider client not enabled in this build")
