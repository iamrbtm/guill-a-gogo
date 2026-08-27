from __future__ import annotations

import uuid

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class TravelerProfile(UUIDMixin, TimestampMixin, Base):
    """Reusable traveler profile. Medical fields are optional and privacy-gated."""

    __tablename__ = "traveler_profiles"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    emergency_contact: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    max_walking_distance_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mobility_devices: Mapped[list | None] = mapped_column(JSON, nullable=True)
    transfer_needs: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accessible_restroom_needs: Mapped[str | None] = mapped_column(String(500), nullable=True)
    preferred_break_frequency_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_break_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sensory_considerations: Mapped[str | None] = mapped_column(String(500), nullable=True)
    routine_preferences: Mapped[str | None] = mapped_column(String(500), nullable=True)
    food_allergies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    dietary_restrictions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Medical (restricted): only authorized trip members; excluded from logs/exports.
    medication_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    emergency_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    privacy_level: Mapped[str] = mapped_column(String(20), default="family", nullable=False)
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Pet(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "pets"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    species: Mapped[str | None] = mapped_column(String(80), nullable=True)
    breed: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size: Mapped[str | None] = mapped_column(String(40), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    hotel_restrictions: Mapped[str | None] = mapped_column(String(500), nullable=True)
    break_frequency_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feeding_schedule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    medication_schedule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vaccination_doc_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    emergency_vet_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Vehicle(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "vehicles"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    make: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    trim: Mapped[str | None] = mapped_column(String(120), nullable=True)
    engine: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tank_capacity_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    normal_mpg: Mapped[float | None] = mapped_column(Float, nullable=True)
    towing_mpg: Mapped[float | None] = mapped_column(Float, nullable=True)
    rated_towing_capacity_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload_limit_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailer_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    loaded_trailer_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    range_safety_reserve_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_cost_safety_margin_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Trailer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "trailers"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    empty_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    loaded_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    length_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Preference(UUIDMixin, TimestampMixin, Base):
    """Default trip-planning preferences for a user."""

    __tablename__ = "preferences"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    target_daily_driving_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    break_frequency_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hotel_budget_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meal_style: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sightseeing_interests: Mapped[list | None] = mapped_column(JSON, nullable=True)
    preferred_arrival_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    scenic_route_tolerance: Mapped[str | None] = mapped_column(String(20), nullable=True)
    max_detour_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_nav_app: Mapped[str | None] = mapped_column(String(40), nullable=True)
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
