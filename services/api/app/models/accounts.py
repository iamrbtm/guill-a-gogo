from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, LargeBinary, String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin, utcnow


def _utc(dt: datetime | None) -> datetime | None:
    return dt.replace(tzinfo=timezone.utc) if dt and dt.tzinfo is None else dt


def func_now():
    from sqlalchemy import func

    return func.now()


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # soft deletion
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    passkeys: Mapped[list["PasskeyCredential"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class PasskeyCredential(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "passkey_credentials"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True, nullable=False, index=True)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transports: Mapped[list | None] = mapped_column(JSON, nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    backed_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="passkeys")


class Invitation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "invitations"

    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    issuer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="traveler", nullable=False)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_expired(self) -> bool:
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp <= utcnow()


class RecoveryToken(UUIDMixin, Base):
    __tablename__ = "recovery_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func_now(), nullable=False)


class RecoveryCode(UUIDMixin, Base):
    __tablename__ = "recovery_codes"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func_now(), nullable=False)


class RefreshSession(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "refresh_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    device_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(400), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="refresh_sessions")


class Trip(UUIDMixin, TimestampMixin, Base):
    """Minimal trip table for FK integrity in Phase 1.

    Full itinerary schema arrives in Phase 2. Soft deletion and owner are
    established here because memberships and audit events reference trips.
    """

    __tablename__ = "trips"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    timezone_policy: Mapped[str] = mapped_column(String(64), default="America/New_York", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class TripMembership(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "trip_memberships"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), default="traveler", nullable=False)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func_now(), nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func_now(), nullable=False, index=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    object_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    object_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

