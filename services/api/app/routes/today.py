from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.itinerary import ChangeProposal, OfflineMutation
from app.services import delays as delay_service
from app.services import sync as sync_service
from app.services.current_user import resolve_current_user
from app.services.planner import PlanConfig, plan_trip_from_db
from app.services.providers.routing import ProviderUnavailable, get_routing_provider
from app.services.serialization import to_dict
from app.services.today import build_today_dashboard, generate_nav_url
from app.services.trip_service import get_trip

bp = Blueprint("today", __name__, url_prefix="/api/v1")


def _db() -> Session:
    return next(get_db())


@bp.route("/trips/<uuid:trip_id>/today", methods=["GET"])
def today(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    trip = get_trip(db, user, trip_id)
    if trip is None:
        return jsonify(error="not_found"), 404
    return jsonify(build_today_dashboard(db, trip))


@bp.route("/trips/<uuid:trip_id>/nav", methods=["GET"])
def nav(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    trip = get_trip(db, user, trip_id)
    if trip is None:
        return jsonify(error="not_found"), 404
    origin = request.args.get("from") or trip.origin or ""
    destination = request.args.get("to") or trip.destination or ""
    provider = request.args.get("provider", "google")
    if not (origin and destination):
        return jsonify(error="missing_from_or_to"), 400
    return jsonify({"provider": provider, "url": generate_nav_url(provider, origin, destination)})


@bp.route("/trips/<uuid:trip_id>/delays", methods=["POST"])
def create_delay(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    trip = get_trip(db, user, trip_id)
    if trip is None:
        return jsonify(error="not_found"), 404
    body = request.get_json(silent=True) or {}
    delay = int(body.get("delay_minutes", 0))
    if delay <= 0:
        return jsonify(error="delay_minutes_required"), 400
    proposal = delay_service.propose_delay_revision(db, trip, delay, user)
    db.commit()
    return jsonify(to_dict(proposal)), 201


@bp.route("/trips/<uuid:trip_id>/proposals", methods=["GET"])
def list_proposals(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    trip = get_trip(db, user, trip_id)
    if trip is None:
        return jsonify(error="not_found"), 404
    rows = db.query(ChangeProposal).filter_by(trip_id=trip_id).all()
    return jsonify([to_dict(p) for p in rows])


@bp.route("/trips/<uuid:trip_id>/proposals/<uuid:proposal_id>/approve", methods=["POST"])
def approve(trip_id: uuid.UUID, proposal_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    proposal = delay_service.approve_proposal(db, proposal_id, user)
    db.commit()
    return jsonify(to_dict(proposal))


@bp.route("/trips/<uuid:trip_id>/proposals/<uuid:proposal_id>/reject", methods=["POST"])
def reject(trip_id: uuid.UUID, proposal_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    proposal = delay_service.reject_proposal(db, proposal_id, user)
    db.commit()
    return jsonify(to_dict(proposal))


@bp.route("/trips/<uuid:trip_id>/sync", methods=["POST"])
def sync(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    body = request.get_json(silent=True) or {}
    mutations = body.get("mutations", [])
    queued = []
    for m in mutations:
        queued.append(
            sync_service.enqueue_mutation(
                db,
                trip_id=trip_id,
                idempotency_key=m["idempotency_key"],
                entity_type=m["entity_type"],
                entity_id=uuid.UUID(m["entity_id"]) if m.get("entity_id") else None,
                operation=m.get("operation", "update"),
                payload=m.get("payload", {}),
                base_version=m.get("base_version"),
                user_id=user.id,
            )
        )
    db.commit()
    # Process the outbox now (server has connectivity). Report each queued
    # mutation's final status (including already-applied idempotent duplicates).
    sync_service.process_outbox(db, trip_id, user)
    db.commit()
    return jsonify(
        {
            "processed": [
                {"id": str(m.id), "status": m.status, "error": m.error} for m in queued
            ]
        }
    )
