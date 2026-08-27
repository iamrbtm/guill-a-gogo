import os
import uuid

import pytest

# Configure a test environment BEFORE importing the app so get_settings() and
# the module-level engine use SQLite and safe test defaults.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("RP_ID", "localhost")
os.environ.setdefault("RP_ORIGIN", "http://localhost:3000")
os.environ.setdefault("AI_PROVIDER", "none")
os.environ.setdefault("EMAIL_PROVIDER", "console")


@pytest.fixture()
def app():
    from app import create_app
    from app.db.session import init_db

    application = create_app()
    # Engine is set on the extensions module by create_app(); read it after.
    from app.extensions import engine

    init_db(engine)
    application.config["TESTING"] = True
    application.config["db_engine"] = engine
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    from app.db.session import get_sessionmaker, init_db

    eng = app.config["db_engine"]
    init_db(eng)
    Session = get_sessionmaker(eng)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def owner_user(db_session):
    from app.models.accounts import User

    user = User(email="owner@example.com", display_name="Owner", status="active")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def owner_auth_headers(owner_user, db_session):
    import jwt
    from app.config import get_settings

    token, _ = (
        __import__("app.services.auth_service", fromlist=["issue_access_token"]).issue_access_token(
            owner_user.id, get_settings()
        )
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def make_user(db_session):
    from app.models.accounts import User

    def _make(email: str):
        u = User(email=email, display_name=email, status="active")
        db_session.add(u)
        db_session.flush()
        return u

    return _make


@pytest.fixture()
def auth_header():
    from app.config import get_settings
    from app.services.auth_service import issue_access_token

    def _header(user):
        token, _ = issue_access_token(user.id, get_settings())
        return {"Authorization": f"Bearer {token}"}

    return _header
