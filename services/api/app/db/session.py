from __future__ import annotations

from collections.abc import Generator

from flask import Flask, g
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.db.base import Base


def make_engine(settings: Settings) -> Engine:
    # PostgreSQL 17 with psycopg 3 driver. Connectivity timeouts keep the
    # API process from hanging on an unavailable database.
    return Engine(  # pragma: no cover - thin wrapper
        _create_engine(settings),
    )


def _create_engine(settings: Settings):
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    connect_args = {"connect_timeout": 10, "options": "-c timezone=utc"}
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args,
    )


def init_db(engine: Engine) -> None:
    # Import models so they register on Base before create_all (dev/test only).
    from app import models  # noqa: F401

    Base.metadata.create_all(engine)


def get_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Request-scoped session dependency for Flask routes."""
    session = g.pop("_db_session", None)
    if session is None:
        from app.extensions import engine

        session = get_sessionmaker(engine)()
        g._db_session = session
    try:
        yield session
    finally:
        session.close()
        g.pop("_db_session", None)
