import os
import tempfile

from alembic import command
from alembic.config import Config
import pytest

from app.db.base import Base


@pytest.fixture()
def alembic_config():
    # Point Alembic at a throwaway SQLite file DB for upgrade/downgrade testing.
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    url = f"sqlite:///{path}"
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    yield cfg, url
    if os.path.exists(path):
        os.remove(path)


def test_migration_upgrade_downgrade(alembic_config):
    cfg, url = alembic_config
    command.upgrade(cfg, "head")
    # After upgrade, all tables from the current metadata should exist.
    from sqlalchemy import create_engine, inspect

    engine = create_engine(url)
    names = set(inspect(engine).get_table_names())
    expected = {
        "users", "passkey_credentials", "invitations", "recovery_tokens",
        "recovery_codes", "refresh_sessions", "trips", "trip_memberships",
        "audit_events", "traveler_profiles", "pets", "vehicles", "trailers",
        "preferences", "trip_days", "stops", "lodging_candidates", "meal_plans",
        "reservations", "expenses", "planning_warnings", "trip_travelers",
        "trip_pets", "alembic_version",
    }
    assert expected.issubset(names), expected - names

    command.downgrade(cfg, "base")
    names_after = set(inspect(engine).get_table_names())
    assert "users" not in names_after
    engine.dispose()
