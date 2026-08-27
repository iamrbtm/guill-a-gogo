from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.itinerary import ChangeProposal
from app.services import ai as ai_service
from app.services import provider_records
from app.services.current_user import resolve_current_user
from app.services.providers.research import get_fuel_price, get_weather, search_places
from app.services.providers.routing import ProviderUnavailable
from app.services.serialization import to_dict
from app.services.trip_service import get_trip

bp = Blueprint("research", __name__, url_prefix="/api/v1")


def _db() -> Session:
    return next(get_db())


@bp.route("/trips/<uuid:trip_id>/ai/propose", methods=["POST"])
def ai_propose(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    trip = get_trip(db, user, trip_id)
    if trip is None:
        return jsonify(error="not_found"), 404

    body = request.get_json(silent=True) or {}
    ai_output = body.get("ai_output")
    if ai_output is None:
        # No inline output: attempt a live provider call (disabled by default).
        try:
            ai_service.generate_ai_proposal(db, trip, body, user)
        except ProviderUnavailable as exc:
            return jsonify(error="ai_unavailable", message=str(exc),
                          guidance="Provide a validated ai_output payload, or enable an AI provider."), 503

    try:
        parsed = ai_service.validate_ai_output(ai_output)
    except ValidationError as exc:
        return jsonify(error="invalid_ai_output", detail=exc.errors()), 422

    # Persist as a PENDING proposal. It never mutates the itinerary until an
    # Owner/Editor approves (reuses the existing proposal approval flow).
    proposal = ai_service.build_ai_proposal(db, trip, parsed, user)
    db.commit()
    return jsonify(to_dict(proposal)), 201


@bp.route("/trips/<uuid:trip_id>/fuel", methods=["GET"])
def fuel(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    if get_trip(db, user, trip_id) is None:
        return jsonify(error="not_found"), 404
    try:
        price = get_fuel_price(location=request.args.get("location"))
        return jsonify({"status": "live", "price_per_gallon": price})
    except ProviderUnavailable:
        return jsonify(
            status="manual_entry",
            message="No fuel provider configured. Enter the price manually; it will be marked as a manual value, not a live station result.",
        ), 200


@bp.route("/trips/<uuid:trip_id>/weather", methods=["GET"])
def weather(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    if get_trip(db, user, trip_id) is None:
        return jsonify(error="not_found"), 404
    try:
        w = get_weather(location=request.args.get("location"))
        return jsonify({"status": "live", "weather": w})
    except ProviderUnavailable:
        return jsonify(
            status="manual_entry",
            message="No weather provider configured. Show the last known outlook and mark it stale; do not present assumed conditions.",
        ), 200


@bp.route("/trips/<uuid:trip_id>/places", methods=["GET"])
def places(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    if get_trip(db, user, trip_id) is None:
        return jsonify(error="not_found"), 404
    try:
        results = search_places(query=request.args.get("q", ""), location=request.args.get("location"))
        return jsonify({"status": "live", "results": results})
    except ProviderUnavailable:
        return jsonify(
            status="manual_entry",
            message="No places provider configured. Google Places is useful for discovery but is NOT proof of room inventory, rates, or ADA configuration. Use manual entry + call checklist.",
        ), 200
