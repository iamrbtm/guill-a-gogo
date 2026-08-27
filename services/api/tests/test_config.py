from app.config import get_settings


def test_settings_defaults():
    s = get_settings()
    assert s.access_token_ttl_seconds == 900
    assert s.refresh_token_ttl_seconds > s.access_token_ttl_seconds
    assert s.ai_provider == "none"
    assert s.email_provider == "console"
    assert s.is_test is True
    assert s.is_production is False


def test_settings_production_flag():
    import importlib

    import app.config as cfg

    old = dict(cfg.os.environ)
    try:
        cfg.os.environ["APP_ENV"] = "production"
        s = cfg.get_settings()
        assert s.is_production is True
    finally:
        cfg.os.environ.clear()
        cfg.os.environ.update(old)
