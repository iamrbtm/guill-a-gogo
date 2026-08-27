from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.current_user import resolve_current_user
from app.services import expense_service, trip_service
from app.services.serialization import to_dict

bp = Blueprint("trips", __name__, url_prefix="/api/v1")


def _db() -> Session:
    return next(get_db())


def _user():
    return resolve_current_user(_db())


@bp.route("/trips", methods=["POST"])
def create_trip():
    db = _db()
    user = resolve_current_user(db)
    data = request.get_json(silent=True) or {}
    trip = trip_service.create_trip(db, user, data)
    db.commit()
    return jsonify(to_dict(trip)), 201


@bp.route("/trips", methods=["GET"])
def list_trips():
    db = _db()
    user = resolve_current_user(db)
    trips = trip_service.list_user_trips(db, user)
    return jsonify([to_dict(t) for t in trips])


@bp.route("/trips/<uuid:trip_id>", methods=["GET"])
def get_trip(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    trip = trip_service.get_trip(db, user, trip_id)
    if trip is None:
        return jsonify(error="not_found"), 404
    return jsonify(to_dict(trip))


@bp.route("/trips/<uuid:trip_id>", methods=["PATCH"])
def update_trip(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    data = request.get_json(silent=True) or {}
    trip = trip_service.update_trip(db, user, trip_id, data)
    if trip is None:
        return jsonify(error="not_found"), 404
    db.commit()
    return jsonify(to_dict(trip))


@bp.route("/trips/<uuid:trip_id>/members", methods=["POST"])
def add_member(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    body = request.get_json(silent=True) or {}
    target = body.get("user_id")
    role = body.get("role", "traveler")
    if not target:
        return jsonify(error="user_id_required"), 400
    try:
        m = trip_service.add_member(db, user, trip_id, uuid.UUID(target), role)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    db.commit()
    return jsonify(to_dict(m)), 201


@bp.route("/trips/<uuid:trip_id>/members/<uuid:target_id>", methods=["DELETE"])
def remove_member(trip_id: uuid.UUID, target_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    try:
        ok = trip_service.remove_member(db, user, trip_id, target_id)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    if not ok:
        return jsonify(error="not_found"), 404
    db.commit()
    return jsonify(status="ok")


@bp.route("/trips/<uuid:trip_id>/vehicle", methods=["POST"])
def assign_vehicle(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    body = request.get_json(silent=True) or {}
    try:
        trip = trip_service.assign_vehicle(db, user, trip_id, uuid.UUID(body["vehicle_id"]))
    except (KeyError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    db.commit()
    return jsonify(to_dict(trip))


@bp.route("/trips/<uuid:trip_id>/trailer", methods=["POST"])
def assign_trailer(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    body = request.get_json(silent=True) or {}
    try:
        trip = trip_service.assign_trailer(db, user, trip_id, uuid.UUID(body["trailer_id"]))
    except (KeyError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    db.commit()
    return jsonify(to_dict(trip))


@bp.route("/trips/<uuid:trip_id>/travelers", methods=["POST"])
def link_traveler(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    body = request.get_json(silent=True) or {}
    try:
        trip_service.link_traveler(db, user, trip_id, uuid.UUID(body["traveler_id"]))
    except (KeyError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    db.commit()
    return jsonify(status="ok"), 201


@bp.route("/trips/<uuid:trip_id>/pets", methods=["POST"])
def link_pet(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    body = request.get_json(silent=True) or {}
    try:
        trip_service.link_pet(db, user, trip_id, uuid.UUID(body["pet_id"]))
    except (KeyError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    db.commit()
    return jsonify(status="ok"), 201


@bp.route("/trips/<uuid:trip_id>/warnings", methods=["GET"])
def get_warnings(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    warnings = expense_service.list_warnings(db, user, trip_id)
    return jsonify([to_dict(w) for w in warnings])


@bp.route("/trips/<uuid:trip_id>/warnings/refresh", methods=["POST"])
def refresh_warnings(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    warnings = expense_service.refresh_trip_warnings(db, user, trip_id)
    db.commit()
    return jsonify([to_dict(w) for w in warnings])
