from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.current_user import resolve_current_user
from app.services import profile_service
from app.services.serialization import to_dict

bp = Blueprint("profiles", __name__, url_prefix="/api/v1")
KINDS = {"traveler", "pet", "vehicle", "trailer", "preference"}


def _db() -> Session:
    return next(get_db())


@bp.route("/profiles/<kind>", methods=["GET"])
def list_profiles(kind: str):
    if kind not in KINDS:
        return jsonify(error="unknown_profile_kind"), 404
    db = _db()
    user = resolve_current_user(db)
    rows = profile_service.list_profiles(db, user, kind)
    return jsonify([to_dict(r) for r in rows])


@bp.route("/profiles/<kind>", methods=["POST"])
def create_profile(kind: str):
    if kind not in KINDS:
        return jsonify(error="unknown_profile_kind"), 404
    db = _db()
    user = resolve_current_user(db)
    data = request.get_json(silent=True) or {}
    obj = profile_service.create_profile(db, user, kind, data)
    db.commit()
    return jsonify(to_dict(obj)), 201


@bp.route("/profiles/<kind>/<uuid:profile_id>", methods=["GET"])
def get_profile(kind: str, profile_id: uuid.UUID):
    if kind not in KINDS:
        return jsonify(error="unknown_profile_kind"), 404
    db = _db()
    user = resolve_current_user(db)
    obj = profile_service.get_profile(db, user, kind, profile_id)
    if obj is None:
        return jsonify(error="not_found"), 404
    return jsonify(to_dict(obj))


@bp.route("/profiles/<kind>/<uuid:profile_id>", methods=["PUT", "PATCH"])
def update_profile(kind: str, profile_id: uuid.UUID):
    if kind not in KINDS:
        return jsonify(error="unknown_profile_kind"), 404
    db = _db()
    user = resolve_current_user(db)
    data = request.get_json(silent=True) or {}
    obj = profile_service.update_profile(db, user, kind, profile_id, data)
    if obj is None:
        return jsonify(error="not_found"), 404
    db.commit()
    return jsonify(to_dict(obj))


@bp.route("/profiles/<kind>/<uuid:profile_id>", methods=["DELETE"])
def delete_profile(kind: str, profile_id: uuid.UUID):
    if kind not in KINDS:
        return jsonify(error="unknown_profile_kind"), 404
    db = _db()
    user = resolve_current_user(db)
    ok = profile_service.delete_profile(db, user, kind, profile_id)
    if not ok:
        return jsonify(error="not_found"), 404
    db.commit()
    return jsonify(status="ok")
