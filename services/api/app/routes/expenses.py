from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.current_user import resolve_current_user
from app.services import expense_service
from app.services.serialization import to_dict

bp = Blueprint("expenses", __name__, url_prefix="/api/v1")


def _db() -> Session:
    return next(get_db())


@bp.route("/trips/<uuid:trip_id>/expenses", methods=["POST"])
def add_expense(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    exp = expense_service.add_expense(db, user, trip_id, request.get_json(silent=True) or {})
    db.commit()
    return jsonify(to_dict(exp)), 201


@bp.route("/trips/<uuid:trip_id>/expenses", methods=["GET"])
def list_expenses(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    return jsonify([to_dict(e) for e in expense_service.list_expenses(db, user, trip_id)])
