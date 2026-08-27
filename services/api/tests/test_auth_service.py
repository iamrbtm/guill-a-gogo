import uuid

from app.config import get_settings
from app.models.accounts import RecoveryCode, RefreshSession, User
from app.services import auth_service, crypto
from app.services.auth_service import consume_recovery_code, issue_token_pair, rotate_refresh


def test_recovery_code_consume(db_session):
    settings = get_settings()
    user = User(email="rc@example.com", display_name="RC", status="active")
    db_session.add(user)
    db_session.flush()

    code = crypto.generate_recovery_code()
    _mod = __import__("datetime")
    db_session.add(
        RecoveryCode(
            user_id=user.id,
            code_hash=crypto.sha256_hex(code),
            expires_at=_mod.datetime.now(_mod.timezone.utc) + _mod.timedelta(days=1),
        )
    )
    db_session.commit()

    assert consume_recovery_code(db_session, user=user, code=code, settings=settings) is True
    # second use fails (single-use)
    assert consume_recovery_code(db_session, user=user, code=code, settings=settings) is False


def test_refresh_rotation_revocates_old(db_session):
    settings = get_settings()
    user = User(email="rt@example.com", display_name="RT", status="active")
    db_session.add(user)
    db_session.flush()

    pair = issue_token_pair(
        db_session, user_id=user.id, device_name="test", user_agent="ua", ip_address="1.2.3.4", settings=settings
    )
    old_refresh = pair["refresh_token"]
    new_pair = rotate_refresh(db_session, raw_token=old_refresh, settings=settings, user_agent="ua", ip_address="1.2.3.4")
    assert new_pair["refresh_token"] != old_refresh

    # Old refresh must now be rejected (revoked by rotation).
    try:
        rotate_refresh(db_session, raw_token=old_refresh, settings=settings, user_agent="ua", ip_address="1.2.3.4")
        assert False, "old refresh should be rejected"
    except ValueError as exc:
        assert "invalid_refresh_token" in str(exc)


def test_access_token_verifies(db_session):
    settings = get_settings()
    user = User(email="at@example.com", display_name="AT", status="active")
    db_session.add(user)
    db_session.flush()
    token, jti = auth_service.issue_access_token(user.id, settings)
    import jwt

    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    assert uuid.UUID(payload["sub"]) == user.id
    assert payload["type"] == "access"
