from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.current_user import resolve_current_user
from app.services import plan_service
from app.services.serialization import to_dict

bp = Blueprint("plan", __name__, url_prefix="/api/v1")


def _db() -> Session:
    return next(get_db())


@bp.route("/trips/<uuid:trip_id>/days", methods=["POST"])
def create_day(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    day = plan_service.create_trip_day(db, user, trip_id, request.get_json(silent=True) or {})
    db.commit()
    return jsonify(to_dict(day)), 201


@bp.route("/trips/<uuid:trip_id>/days", methods=["GET"])
def list_days(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    return jsonify([to_dict(d) for d in plan_service.list_trip_days(db, user, trip_id)])


@bp.route("/trips/<uuid:trip_id>/days/<uuid:day_id>", methods=["PATCH"])
def update_day(trip_id: uuid.UUID, day_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    day = plan_service.update_trip_day(db, user, trip_id, day_id, request.get_json(silent=True) or {})
    if day is None:
        return jsonify(error="not_found"), 404
    db.commit()
    return jsonify(to_dict(day))


@bp.route("/trips/<uuid:trip_id>/stops", methods=["POST"])
def create_stop(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    stop = plan_service.create_stop(db, user, trip_id, request.get_json(silent=True) or {})
    db.commit()
    return jsonify(to_dict(stop)), 201


@bp.route("/trips/<uuid:trip_id>/stops", methods=["GET"])
def list_stops(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    return jsonify([to_dict(s) for s in plan_service.list_stops(db, user, trip_id)])


@bp.route("/trips/<uuid:trip_id>/stops/<uuid:stop_id>", methods=["PATCH"])
def update_stop(trip_id: uuid.UUID, stop_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    stop = plan_service.update_stop(db, user, trip_id, stop_id, request.get_json(silent=True) or {})
    if stop is None:
        return jsonify(error="not_found"), 404
    db.commit()
    return jsonify(to_dict(stop))


@bp.route("/trips/<uuid:trip_id>/lodging", methods=["POST"])
def create_lodging(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    lodg = plan_service.create_lodging(db, user, trip_id, request.get_json(silent=True) or {})
    db.commit()
    return jsonify(to_dict(lodg)), 201


@bp.route("/trips/<uuid:trip_id>/lodging", methods=["GET"])
def list_lodging(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    return jsonify([to_dict(l) for l in plan_service.list_lodging(db, user, trip_id)])


@bp.route("/trips/<uuid:trip_id>/lodging/<uuid:lodging_id>/confirm", methods=["POST"])
def confirm_lodging(trip_id: uuid.UUID, lodging_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    lodg = plan_service.confirm_lodging(db, user, trip_id, lodging_id, request.get_json(silent=True) or {})
    if lodg is None:
        return jsonify(error="not_found"), 404
    db.commit()
    return jsonify(to_dict(lodg))


@bp.route("/trips/<uuid:trip_id>/meals", methods=["POST"])
def create_meal(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    meal = plan_service.create_meal(db, user, trip_id, request.get_json(silent=True) or {})
    db.commit()
    return jsonify(to_dict(meal)), 201


@bp.route("/trips/<uuid:trip_id>/meals", methods=["GET"])
def list_meals(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    return jsonify([to_dict(m) for m in plan_service.list_meals(db, user, trip_id)])


@bp.route("/trips/<uuid:trip_id>/reservations", methods=["POST"])
def create_reservation(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    res = plan_service.create_reservation(db, user, trip_id, request.get_json(silent=True) or {})
    db.commit()
    return jsonify(to_dict(res)), 201


@bp.route("/trips/<uuid:trip_id>/reservations", methods=["GET"])
def list_reservations(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    return jsonify([to_dict(r) for r in plan_service.list_reservations(db, user, trip_id)])
