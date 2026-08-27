from __future__ import annotations

from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import Engine

from app.config import get_settings

settings = get_settings()

# Engine is created once per process. In tests this is overridden before
# the app is built (see tests/conftest.py).
engine: Engine = None  # type: ignore[assignment]

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])

cors = CORS()


def create_engine_for_settings(s: object = settings) -> Engine:
    from app.db.session import _create_engine

    return _create_engine(s)  # type: ignore[arg-type]
