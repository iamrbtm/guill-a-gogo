from __future__ import annotations

import datetime as dt
import uuid
from typing import Optional

import jwt
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.accounts import Invitation, RefreshSession, RecoveryCode, User
from app.services import crypto


def create_invitation(
    session: Session,
    *,
    issuer_id: uuid.UUID,
    role: str,
    email: Optional[str],
    trip_id: Optional[uuid.UUID],
    settings: Settings,
) -> Invitation:
    token = crypto.generate_token(32)
    invitation = Invitation(
        token=token,
        issuer_id=issuer_id,
        email=email,
        role=role,
        trip_id=trip_id,
        status="pending",
        expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=settings.invitation_ttl_seconds),
    )
    session.add(invitation)
    session.flush()
    return invitation


def issue_access_token(user_id: uuid.UUID, settings: Settings) -> tuple[str, str]:
    jti = crypto.generate_token(16)
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(seconds=settings.access_token_ttl_seconds)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, jti


def create_refresh_session(
    session: Session,
    *,
    user_id: uuid.UUID,
    device_name: Optional[str],
    user_agent: Optional[str],
    ip_address: Optional[str],
    settings: Settings,
) -> str:
    raw = crypto.generate_token(48)
    jti = crypto.generate_token(16)
    session.add(
        RefreshSession(
            user_id=user_id,
            token_hash=crypto.sha256_hex(raw),
            jti=jti,
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=dt.datetime.now(dt.timezone.utc)
            + dt.timedelta(seconds=settings.refresh_token_ttl_seconds),
        )
    )
    session.flush()
    return raw


def issue_token_pair(
    session: Session,
    *,
    user_id: uuid.UUID,
    device_name: Optional[str],
    user_agent: Optional[str],
    ip_address: Optional[str],
    settings: Settings,
) -> dict:
    access, _ = issue_access_token(user_id, settings)
    refresh = create_refresh_session(
        session,
        user_id=user_id,
        device_name=device_name,
        user_agent=user_agent,
        ip_address=ip_address,
        settings=settings,
    )
    return {"access_token": access, "refresh_token": refresh, "token_type": "Bearer"}


def rotate_refresh(
    session: Session,
    *,
    raw_token: str,
    settings: Settings,
    user_agent: Optional[str],
    ip_address: Optional[str],
) -> dict:
    token_hash = crypto.sha256_hex(raw_token)
    record = (
        session.query(RefreshSession)
        .filter_by(token_hash=token_hash, revoked_at=None)
        .first()
    )
    if record is None:
        raise ValueError("invalid_refresh_token")
    if _tz_aware(record.expires_at) <= dt.datetime.now(dt.timezone.utc):
        raise ValueError("refresh_token_expired")

    import uuid as _uuid

    uid = uuid.UUID(str(record.user_id))
    if settings.session_rotation_enabled:
        record.revoked_at = dt.datetime.now(dt.timezone.utc)
    record.last_used_at = dt.datetime.now(dt.timezone.utc)
    return issue_token_pair(
        session,
        user_id=uid,
        device_name=record.device_name,
        user_agent=user_agent,
        ip_address=ip_address,
        settings=settings,
    )


def revoke_refresh(session: Session, *, raw_token: str) -> None:
    token_hash = crypto.sha256_hex(raw_token)
    record = session.query(RefreshSession).filter_by(token_hash=token_hash).first()
    if record is not None:
        record.revoked_at = dt.datetime.now(dt.timezone.utc)


def _tz_aware(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value


def consume_recovery_code(session: Session, *, user: User, code: str, settings: Settings) -> bool:
    code_hash = crypto.sha256_hex(code.strip().upper())
    record = (
        session.query(RecoveryCode)
        .filter_by(user_id=user.id, code_hash=code_hash, used_at=None)
        .first()
    )
    if record is None:
        return False
    if _tz_aware(record.expires_at) <= dt.datetime.now(dt.timezone.utc):
        return False
    record.used_at = dt.datetime.now(dt.timezone.utc)
    session.flush()
    return True
