from __future__ import annotations

from app.models.profiles import Trailer, Vehicle

# Fields required before a vehicle can be considered planning-ready. The earlier
# "2001 Volkswagen Atlas Cross Sport" seed (impossible model/year) must stay
# incomplete until the family supplies real values — we never guess them.
VEHICLE_REQUIRED_FIELDS = {
    "year": "model year",
    "make": "make",
    "model": "model",
    "towing_mpg": "towing MPG",
    "rated_towing_capacity_kg": "rated towing capacity",
    "loaded_trailer_weight_kg": "loaded trailer weight",
}


def evaluate_vehicle(vehicle: Vehicle) -> list[dict]:
    """Return deterministic warnings for a vehicle. An empty list means ready."""
    warnings: list[dict] = []
    missing = [label for field, label in VEHICLE_REQUIRED_FIELDS.items() if getattr(vehicle, field) is None]
    if not vehicle.trim and not vehicle.engine:
        missing.append("trim or engine")

    if missing:
        warnings.append(
            {
                "category": "vehicle_incomplete",
                "severity": "blocking",
                "message": "Vehicle profile is incomplete and cannot be used for towing planning until these are provided: "
                + ", ".join(missing)
                + ". Do not guess the correct vehicle, fuel economy, towing capacity, or trailer weight.",
            }
        )
        return warnings

    # Towing safety: never inferred from model name alone.
    if (vehicle.loaded_trailer_weight_kg or 0) > (vehicle.rated_towing_capacity_kg or 0):
        warnings.append(
            {
                "category": "towing_overload",
                "severity": "blocking",
                "message": (
                    f"Loaded trailer weight ({vehicle.loaded_trailer_weight_kg} kg) exceeds rated "
                    f"towing capacity ({vehicle.rated_towing_capacity_kg} kg). Reduce load or choose a "
                    "different tow vehicle before planning."
                ),
            }
        )

    if vehicle.towing_mpg and vehicle.towing_mpg <= 0:
        warnings.append(
            {
                "category": "vehicle_invalid",
                "severity": "blocking",
                "message": "Towing MPG must be greater than zero.",
            }
        )

    return warnings


def evaluate_trailer(trailer: Trailer) -> list[dict]:
    warnings: list[dict] = []
    if trailer.loaded_weight_kg is None:
        warnings.append(
            {
                "category": "trailer_incomplete",
                "severity": "warning",
                "message": "Trailer loaded weight is unknown; towing safety cannot be verified.",
            }
        )
    return warnings
