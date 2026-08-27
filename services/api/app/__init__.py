from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify, request

from app.config import get_settings
from app.db.session import _create_engine
from app.extensions import cors, engine as _engine, limiter

logger = logging.getLogger("guill")


def create_app(settings=None, engine=None) -> Flask:
    settings = settings or get_settings()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings

    # Engine: use provided (tests) or module-level or create from settings.
    global_engine = engine or _engine or _create_engine(settings)
    import app.extensions as ext

    ext.engine = global_engine

    _register_extensions(app, settings)
    _register_security_headers(app, settings)
    _register_blueprints(app)
    _register_error_handlers(app)

    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok", "service": "api"})

    @app.route("/readyz")
    def readyz():
        try:
            with global_engine.connect() as conn:
                conn.execution_options(  # pragma: no cover
                    logging_name="ready"
                )
                from sqlalchemy import text

                conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception as exc:  # pragma: no cover - depends on live DB
            logger.warning("readiness check failed: %s", exc)
            db_ok = False
        return jsonify({"status": "ok" if db_ok else "degraded", "database": db_ok}), (
            200 if db_ok else 503
        )

    return app


def _register_extensions(app: Flask, settings) -> None:
    cors.init_app(app, resources={r"/api/*": {"origins": settings.cors_allowed_origins}})
    limiter.init_app(app)


def _register_security_headers(app: Flask, settings) -> None:
    from app.security.headers import DEFAULT_SECURE_HEADERS

    @app.after_request
    def _apply_headers(resp):
        for key, value in DEFAULT_SECURE_HEADERS.items():
            resp.headers.set(key, value)
        if settings.is_production:
            resp.headers.set(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )
        return resp


def _register_blueprints(app: Flask) -> None:
    from app.routes import auth, expenses, health, plan, profiles, providers, today, trips

    app.register_blueprint(health.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(providers.bp)
    app.register_blueprint(trips.bp)
    app.register_blueprint(profiles.bp)
    app.register_blueprint(plan.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(today.bp)


def _register_error_handlers(app: Flask) -> None:
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(HTTPException)
    def _handle_http_exc(exc: HTTPException):
        return jsonify(error=exc.name, message=exc.description), exc.code or 500

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        logger.exception("unhandled error: %s", exc)
        return jsonify(error="internal_error", message="Internal server error"), 500


def get_settings_of(app: Flask) -> Any:
    return app.config["SETTINGS"]
