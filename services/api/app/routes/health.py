from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__, url_prefix="/api/v1")


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "api"})
