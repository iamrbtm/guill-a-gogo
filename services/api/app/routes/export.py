from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request, send_file
import io

from app.db.session import get_db
from app.services.current_user import resolve_current_user
from app.services.export import collect_itinerary_data, get_exporter
from app.services.trip_service import get_trip

bp = Blueprint("export", __name__, url_prefix="/api/v1")


def _db():
    return next(get_db())


@bp.route("/trips/<uuid:trip_id>/export", methods=["GET"])
def export_trip(trip_id: uuid.UUID):
    db = _db()
    user = resolve_current_user(db)
    trip = get_trip(db, user, trip_id)
    if trip is None:
        return jsonify(error="not_found"), 404

    fmt = (request.args.get("format") or "csv").lower()
    spec = get_exporter(fmt)
    if spec is None:
        return jsonify(error="unsupported_format", supported=["csv", "xlsx", "pdf", "docx"]), 400
    content_type, filename, fn = spec

    data = collect_itinerary_data(db, trip)
    payload = fn(data)
    return send_file(
        io.BytesIO(payload),
        mimetype=content_type,
        as_attachment=True,
        download_name=filename,
    )


@bp.route("/trips/<uuid:trip_id>/export/drive", methods=["POST"])
def export_to_drive(trip_id: uuid.UUID):
    """Optional Google Drive/Docs delivery via user-authorized OAuth.

    When not configured, local download still works (see /export). This endpoint
    is a stub until a Drive provider is wired up.
    """
    return jsonify(
        error="drive_not_configured",
        message="Google Drive delivery is not configured. Use GET /export?format=docx to download locally.",
    ), 503
