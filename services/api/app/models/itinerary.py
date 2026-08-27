from __future__ import annotations

import uuid

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class TripDay(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "trip_days"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Stop(UUIDMixin, TimestampMixin, Base):
    """Ordered stop on a trip. Used for required/optional places, breaks, fuel, meals."""

    __tablename__ = "stops"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_day_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stop_type: Mapped[str] = mapped_column(String(30), default="optional_place", nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(400), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    arrival_target: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    min_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sequence_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class LodgingCandidate(UUIDMixin, TimestampMixin, Base):
    """A lodging *candidate*. Never mark two-dog/accessibility as confirmed
    unless explicitly confirmed by a human (see confirmed_* fields)."""

    __tablename__ = "lodging_candidates"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(String(400), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    pet_friendly_advertised: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_dogs_permitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight_breed_restrictions_known: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pet_fees_in_total: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accessible_room_listed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    required_accessibility_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    breakfast_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trailer_parking_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rate_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    taxes_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retrieved_for_dates: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmation_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    who_confirmed: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confirmation_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_link: Mapped[str | None] = mapped_column(String(500), nullable=True)


class MealPlan(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "meal_plans"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_day_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=True)
    stop_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("stops.id", ondelete="SET NULL"), nullable=True)
    meal_type: Mapped[str] = mapped_column(String(20), default="dinner", nullable=False)
    restaurant_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(400), nullable=True)
    serves_fish: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fish_safe_option_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_link: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Reservation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "reservations"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    lodging_candidate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lodging_candidates.id", ondelete="SET NULL"), nullable=True)
    activity: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confirmation_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    booker_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    booked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_link: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Expense(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "expenses"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), default="other", nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    incurred_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class PlanningWarning(UUIDMixin, TimestampMixin, Base):
    """Deterministic, human-readable warnings surfaced by the planner.

    Severity 'blocking' must be resolved before an itinerary can be approved.
    """

    __tablename__ = "planning_warnings"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="warning", nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)


class ChangeProposal(UUIDMixin, TimestampMixin, Base):
    """A proposed itinerary change requiring human approval.

    Used by delay handling (and later AI proposals). The stored itinerary is
    NEVER mutated until an Owner/Editor approves. `before`/`after` hold the
    affected schedule slices as JSON.
    """

    __tablename__ = "change_proposals"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), default="delay_revision", nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    before: Mapped[dict] = mapped_column(JSON, nullable=False)
    after: Mapped[dict] = mapped_column(JSON, nullable=False)
    assumptions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OfflineMutation(UUIDMixin, TimestampMixin, Base):
    """Mutation queued on a device while offline; replayed via the sync endpoint.

    Idempotency is enforced by `idempotency_key`. Conflicting edits are detected
    by comparing the entity's current version against `base_version` (optimistic
    concurrency) and surfaced as `conflict` rather than last-write-wins.
    """

    __tablename__ = "offline_mutations"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    operation: Mapped[str] = mapped_column(String(20), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    base_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class ProviderRecord(UUIDMixin, TimestampMixin, Base):
    """Provenance for every external provider result.

    Records what was asked, when, how fresh it is, and how it was verified, so the
    UI can mark data as live/cached/manual and never present stale facts as current.
    """

    __tablename__ = "provider_records"

    trip_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    provider_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    request_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    retrieved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    normalized_response: Mapped[dict] = mapped_column(JSON, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified", nullable=False)
    source_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
