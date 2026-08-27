from __future__ import annotations

import base64
import datetime as dt
import uuid

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy.orm import Session
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import AuthenticatorSelectionCriteria, ResidentKeyRequirement

from app.config import get_settings
from app.db.session import get_db
from app.models.accounts import Invitation, PasskeyCredential, RecoveryCode, User
from app.services import crypto
from app.services.audit import record_audit
from app.services.auth_service import (
    consume_recovery_code,
    create_invitation,
    issue_access_token,
    issue_token_pair,
    revoke_refresh,
    rotate_refresh,
)
from app.services.challenge_store import challenge_store
from app.services.email import notify_invitation, notify_recovery

bp = Blueprint("auth", __name__, url_prefix="/api/v1")


def _client_ip() -> str | None:
    return request.remote_addr


def _user_agent() -> str | None:
    return request.headers.get("User-Agent")


def _current_user_id() -> uuid.UUID | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[len("Bearer ") :]
    try:
        s = get_settings()
        payload = __import__("jwt").decode(token, s.jwt_secret, algorithms=["HS256"])
    except Exception:
        return None
    if payload.get("type") != "access":
        return None
    return uuid.UUID(payload["sub"])


def _require_user() -> uuid.UUID:
    uid = _current_user_id()
    if uid is None:
        from werkzeug.exceptions import Unauthorized

        raise Unauthorized("valid access token required")
    return uid


# ---------------------------------------------------------------------------
# Invitations (owner-only)
# ---------------------------------------------------------------------------
@bp.route("/invitations", methods=["POST"])
def create_invitation_endpoint():
    issuer = _require_user()
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or None)
    role = body.get("role", "traveler")
    if role not in {"owner", "editor", "traveler", "viewer"}:
        return jsonify(error="invalid_role"), 400
    trip_id = body.get("trip_id")
    db: Session = next(get_db())
    settings = get_settings()
    invitation = create_invitation(
        db, issuer_id=issuer, role=role, email=email, trip_id=uuid.UUID(trip_id) if trip_id else None, settings=settings
    )
    db.commit()
    link = f"{settings.invitation_base_url}?token={invitation.token}"
    if email:
        notify_invitation(email, link, settings)
    record_audit(db, action="invitation.created", actor_user_id=issuer, object_type="invitation", object_id=invitation.id, ip_address=_client_ip())
    db.commit()
    return (
        jsonify(
            {
                "invitation_id": str(invitation.id),
                "token": invitation.token,
                "link": link,
                "expires_at": invitation.expires_at.isoformat(),
                "role": invitation.role,
            }
        ),
        201,
    )


@bp.route("/invitations/<token>", methods=["GET"])
def invitation_details(token):
    db: Session = next(get_db())
    inv = db.query(Invitation).filter_by(token=token).first()
    if inv is None or inv.status != "pending" or inv.is_expired:
        return jsonify(error="invitation_invalid"), 404
    return jsonify(
        {
            "email": inv.email,
            "role": inv.role,
            "expires_at": inv.expires_at.isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# Passkey registration
# ---------------------------------------------------------------------------
@bp.route("/auth/register/options", methods=["POST"])
def register_options():
    body = request.get_json(silent=True) or {}
    token = body.get("invitation_token")
    if not token:
        return jsonify(error="invitation_token_required"), 400
    db: Session = next(get_db())
    inv = db.query(Invitation).filter_by(token=token).first()
    if inv is None or inv.status != "pending" or inv.is_expired:
        return jsonify(error="invitation_invalid"), 404

    new_user_id = uuid.uuid4()
    options = generate_registration_options(
        rp_id=get_settings().rp_id,
        rp_name=get_settings().rp_name,
        user_id=new_user_id.bytes,
        user_name=inv.email or f"user-{new_user_id.hex[:8]}",
        user_display_name=inv.email or "New user",
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED
        ),
    )
    cid = challenge_store.put(new_user_id, "registration", options.challenge)
    return jsonify(
        {
            "challenge_id": cid,
            "publicKey": options_to_json(options),
        }
    )


@bp.route("/auth/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    cid = body.get("challenge_id")
    token = body.get("invitation_token")
    credential = body.get("credential")
    display_name = (body.get("display_name") or "").strip()
    if not (cid and token and credential):
        return jsonify(error="missing_fields"), 400

    ctx = challenge_store.consume(cid)
    if ctx is None or ctx.purpose != "registration":
        return jsonify(error="invalid_challenge"), 400

    db: Session = next(get_db())
    inv = db.query(Invitation).filter_by(token=token).first()
    if inv is None or inv.status != "pending" or inv.is_expired:
        return jsonify(error="invitation_invalid"), 404

    settings = get_settings()
    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=ctx.challenge,
            expected_origin=settings.rp_origin,
            expected_rp_id=settings.rp_id,
            require_user_verification=False,
        )
    except Exception as exc:  # pragma: no cover - depends on client payload
        return jsonify(error="registration_failed", detail=str(exc)), 400

    user = User(
        id=ctx.user_id,
        email=inv.email or f"user-{ctx.user_id.hex[:8]}@pending.local",
        display_name=display_name or (inv.email or "New user"),
        status="active",
    )
    db.add(user)
    db.flush()
    db.add(
        PasskeyCredential(
            user_id=user.id,
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            backed_up=verification.credential_backed_up,
        )
    )
    inv.status = "accepted"
    inv.accepted_user_id = user.id
    inv.accepted_at = dt.datetime.now(dt.timezone.utc)
    db.flush()
    tokens = issue_token_pair(
        db, user_id=user.id, device_name=body.get("device_name"), user_agent=_user_agent(), ip_address=_client_ip(), settings=settings
    )
    record_audit(db, action="account.created", actor_user_id=user.id, object_type="user", object_id=user.id, ip_address=_client_ip())
    record_audit(db, action="passkey.registered", actor_user_id=user.id, object_type="passkey", ip_address=_client_ip())

    recovery_codes = _issue_recovery_codes(db, user, settings)
    db.commit()
    return jsonify({"tokens": tokens, "recovery_codes": recovery_codes}), 201


def _issue_recovery_codes(db: Session, user: User, settings) -> list[str]:
    codes: list[str] = []
    now = dt.datetime.now(dt.timezone.utc)
    for _ in range(settings.recovery_code_count):
        code = crypto.generate_recovery_code()
        codes.append(code)
        db.add(
            RecoveryCode(
                user_id=user.id,
                code_hash=crypto.sha256_hex(code),
                expires_at=now + dt.timedelta(seconds=settings.recovery_code_ttl_seconds),
            )
        )
    return codes


# ---------------------------------------------------------------------------
# Passkey login
# ---------------------------------------------------------------------------
@bp.route("/auth/login/options", methods=["POST"])
def login_options():
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    if not email:
        return jsonify(error="email_required"), 400
    db: Session = next(get_db())
    user = db.query(User).filter_by(email=email, deleted_at=None).first()
    if user is None or user.status != "active":
        return jsonify(error="invalid_credentials"), 404

    allow = [{"id": c.credential_id, "transports": c.transports or []} for c in user.passkeys]
    options = generate_authentication_options(rp_id=get_settings().rp_id, allow_credentials=allow)
    cid = challenge_store.put(user.id, "login", options.challenge)
    return jsonify({"challenge_id": cid, "publicKey": options_to_json(options)})


@bp.route("/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    cid = body.get("challenge_id")
    email = body.get("email")
    credential = body.get("credential")
    if not (cid and email and credential):
        return jsonify(error="missing_fields"), 400

    ctx = challenge_store.consume(cid)
    if ctx is None or ctx.purpose != "login":
        return jsonify(error="invalid_challenge"), 400

    db: Session = next(get_db())
    user = db.query(User).filter_by(email=email, deleted_at=None).first()
    if user is None:
        return jsonify(error="invalid_credentials"), 401

    pk = _find_passkey(db, user, credential)
    if pk is None:
        return jsonify(error="unknown_credential"), 401

    settings = get_settings()
    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=ctx.challenge,
            expected_rp_id=settings.rp_id,
            expected_origin=settings.rp_origin,
            credential_public_key=pk.public_key,
            credential_current_sign_count=pk.sign_count,
            require_user_verification=False,
        )
    except Exception as exc:  # pragma: no cover
        return jsonify(error="authentication_failed", detail=str(exc)), 400

    pk.sign_count = verification.new_sign_count
    pk.last_used_at = dt.datetime.now(dt.timezone.utc)
    tokens = issue_token_pair(
        db, user_id=user.id, device_name=body.get("device_name"), user_agent=_user_agent(), ip_address=_client_ip(), settings=settings
    )
    record_audit(db, action="auth.login", actor_user_id=user.id, ip_address=_client_ip())
    db.commit()
    return jsonify(tokens)


def _b64url_to_bytes(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _find_passkey(db: Session, user: User, credential: dict) -> PasskeyCredential | None:
    raw_id = credential.get("rawId")
    if not raw_id:
        return None
    cid = _b64url_to_bytes(raw_id)
    return db.query(PasskeyCredential).filter_by(user_id=user.id, credential_id=cid).first()


# ---------------------------------------------------------------------------
# Refresh / logout
# ---------------------------------------------------------------------------
@bp.route("/auth/refresh", methods=["POST"])
def refresh():
    body = request.get_json(silent=True) or {}
    raw = body.get("refresh_token")
    if not raw:
        return jsonify(error="refresh_token_required"), 400
    db: Session = next(get_db())
    settings = get_settings()
    try:
        tokens = rotate_refresh(db, raw_token=raw, settings=settings, user_agent=_user_agent(), ip_address=_client_ip())
    except ValueError as exc:
        return jsonify(error=str(exc)), 401
    db.commit()
    return jsonify(tokens)


@bp.route("/auth/logout", methods=["POST"])
def logout():
    body = request.get_json(silent=True) or {}
    raw = body.get("refresh_token")
    if raw:
        db: Session = next(get_db())
        revoke_refresh(db, raw_token=raw)
        db.commit()
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Recovery (single-use recovery codes)
# ---------------------------------------------------------------------------
@bp.route("/auth/recovery/request", methods=["POST"])
def recovery_request():
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    if not email:
        return jsonify(error="email_required"), 400
    db: Session = next(get_db())
    user = db.query(User).filter_by(email=email, deleted_at=None).first()
    if user is None:
        # Do not reveal account existence; return success-shaped response.
        return jsonify({"status": "ok"})
    settings = get_settings()
    # Issue a short-lived recovery token link (stored hashed). For Phase 1 the
    # actual re-registration is performed with recovery codes, so this link is
    # informational and points the user to use a recovery code in the app.
    link = f"{settings.invitation_base_url.replace('/accept', '')}/recover?email={email}"
    notify_recovery(email, link, settings)
    record_audit(db, action="recovery.requested", actor_user_id=user.id, object_type="user", object_id=user.id, ip_address=_client_ip())
    db.commit()
    return jsonify({"status": "ok"})


@bp.route("/auth/recovery-code", methods=["POST"])
def recovery_code_login():
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    code = body.get("code")
    if not (email and code):
        return jsonify(error="missing_fields"), 400
    db: Session = next(get_db())
    user = db.query(User).filter_by(email=email, deleted_at=None).first()
    if user is None:
        return jsonify(error="invalid_credentials"), 401
    if not consume_recovery_code(db, user=user, code=code, settings=get_settings()):
        return jsonify(error="invalid_code"), 401
    access, _ = issue_access_token(user.id, get_settings())
    record_audit(db, action="recovery.used", actor_user_id=user.id, ip_address=_client_ip())
    db.commit()
    return jsonify({"access_token": access, "token_type": "Bearer", "must_register_passkey": True})
