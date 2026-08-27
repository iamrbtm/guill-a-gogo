from __future__ import annotations

import jwt
import uuid

from flask import request
from sqlalchemy.orm import Session
from werkzeug.exceptions import Unauthorized

from app.config import get_settings
from app.models.accounts import User


def resolve_current_user(session: Session) -> User:
    """Load the authenticated User from the Bearer access token.

    Raises 401 if missing/invalid. Authorization is enforced in the service
    layer per object, but authentication happens here.
    """
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise Unauthorized("missing_token")
    token = header[len("Bearer ") :]
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise Unauthorized("invalid_token")
    if payload.get("type") != "access":
        raise Unauthorized("wrong_token_type")
    sub = payload.get("sub")
    if not sub:
        raise Unauthorized("invalid_token")
    user = session.get(User, uuid.UUID(sub))
    if user is None or user.status != "active" or user.deleted_at is not None:
        raise Unauthorized("user_not_found")
    return user
