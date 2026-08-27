from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from typing import Optional


def _env_flag(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Application settings sourced from the environment.

    Secrets come only from the environment or Docker secrets; nothing is
    hard-coded. See infra/.env.example for the documented variable names.
    """

    env: str = field(default_factory=lambda: os.environ.get("APP_ENV", "development"))

    # Database
    database_url: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL", "postgresql+psycopg://app:app@localhost:5432/guill"
        )
    )

    # Redis / Celery
    redis_url: str = field(
        default_factory=lambda: os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    )

    # WebAuthn / passkeys
    rp_name: str = field(default_factory=lambda: os.environ.get("RP_NAME", "Guill-a-Gogo"))
    rp_id: str = field(default_factory=lambda: os.environ.get("RP_ID", "localhost"))
    rp_origin: str = field(
        default_factory=lambda: os.environ.get("RP_ORIGIN", "http://localhost:3000")
    )

    # Tokens / sessions
    jwt_secret: str = field(
        default_factory=lambda: os.environ.get("JWT_SECRET", secrets.token_urlsafe(48))
    )
    access_token_ttl_seconds: int = 900  # 15 minutes
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days
    session_rotation_enabled: bool = True

    # Invitations
    invitation_ttl_seconds: int = 60 * 60 * 24 * 7  # 7 days
    invitation_base_url: str = field(
        default_factory=lambda: os.environ.get(
            "INVITATION_BASE_URL", "https://app.guill.example/accept"
        )
    )

    # Recovery
    recovery_code_count: int = 10
    recovery_code_ttl_seconds: int = 60 * 60 * 24 * 365  # 1 year

    # Email (optional provider; defaults to console logging)
    email_provider: str = field(
        default_factory=lambda: os.environ.get("EMAIL_PROVIDER", "console")
    )
    email_from: str = field(
        default_factory=lambda: os.environ.get("EMAIL_FROM", "no-reply@guill.example")
    )
    smtp_host: Optional[str] = field(
        default_factory=lambda: os.environ.get("SMTP_HOST")
    )
    smtp_port: int = field(
        default_factory=lambda: int(os.environ.get("SMTP_PORT", "587"))
    )
    smtp_user: Optional[str] = field(
        default_factory=lambda: os.environ.get("SMTP_USER")
    )
    smtp_password: Optional[str] = field(
        default_factory=lambda: os.environ.get("SMTP_PASSWORD")
    )

    # AI provider (optional, provider-neutral). `none` disables the layer.
    ai_provider: str = field(
        default_factory=lambda: os.environ.get("AI_PROVIDER", "none")
    )
    ai_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("AI_API_KEY")
    )
    ai_base_url: Optional[str] = field(
        default_factory=lambda: os.environ.get("AI_BASE_URL")
    )
    ai_model: Optional[str] = field(
        default_factory=lambda: os.environ.get("AI_MODEL")
    )

    # Maps / providers (optional; absent -> graceful manual entry)
    google_maps_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("GOOGLE_MAPS_API_KEY")
    )
    # Dev-only: allow the deterministic mock router for local planning demos.
    # Never enable in production (it does not reflect real roads).
    allow_mock_planning: bool = field(
        default_factory=lambda: _env_flag("ALLOW_MOCK_PLANNING", False)
    )

    # Security
    cors_allowed_origins: list[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ]
    )
    rate_limit_default: str = field(
        default_factory=lambda: os.environ.get("RATE_LIMIT_DEFAULT", "200 per hour")
    )

    # Operations
    external_network: str = field(
        default_factory=lambda: os.environ.get("EXTERNAL_NETWORK", "webproxy_net")
    )
    log_level: str = field(
        default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO")
    )

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def is_test(self) -> bool:
        return self.env.lower() == "test"


def get_settings() -> Settings:
    return Settings()
