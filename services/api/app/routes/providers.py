from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("providers", __name__, url_prefix="/api/v1")


@bp.route("/provider-status")
def provider_status():
    """Public-ish status of configured optional providers.

    Never reports secrets; only whether each provider is configured.
    """
    from app.config import get_settings

    s = get_settings()
    return jsonify(
        {
            "providers": {
                "google_maps": bool(s.google_maps_api_key),
                "ai": s.ai_provider if s.ai_provider != "none" else None,
                "email": s.email_provider,
            }
        }
    )
