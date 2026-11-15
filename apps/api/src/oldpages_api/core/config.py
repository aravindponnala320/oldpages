from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Development-only defaults; refuse_unsafe_defaults stops staging/production from using them.
_DEV_JWT_SECRET = "development-only-change-me"  # noqa: S105
_DEV_STORAGE_SECRET = "oldpages-secret"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OLDPAGES_",
        extra="ignore",
    )

    app_name: str = "OldPages API"
    api_v1_prefix: str = "/api/v1"
    access_token_expire_minutes: int = 15
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"]
    )
    database_url: str = "postgresql+asyncpg://oldpages:oldpages@localhost:5432/oldpages"
    # Per process (API and worker each have one). A query running past the timeout is
    # cancelled by Postgres instead of holding a connection while requests queue behind it.
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout_seconds: float = 10.0
    database_statement_timeout_ms: int = 5_000
    debug: bool = False
    environment: Literal["local", "test", "staging", "production"] = "local"
    email_verification_token_hours: int = 24
    email_provider: Literal["resend", "mailjet", "noop"] = "noop"
    email_from: str = "OldPages <noreply@oldpages.in>"
    resend_api_key: SecretStr | None = None
    mailjet_api_key: SecretStr | None = None
    mailjet_secret_key: SecretStr | None = None
    mailjet_sandbox: bool = False
    public_web_url: str = "http://localhost:3000"
    google_client_id: str | None = None
    expose_development_auth_tokens: bool = True
    jwt_algorithm: str = "HS256"
    jwt_secret_key: SecretStr = SecretStr(_DEV_JWT_SECRET)
    log_level: str = "INFO"
    object_storage_access_key: str = "oldpages"
    object_storage_bucket: str = "oldpages-media"
    object_storage_endpoint: str = "http://localhost:9000"
    # Browser-facing storage URL, when it differs from the one the API uses (e.g. in Docker).
    object_storage_public_endpoint: str | None = None
    object_storage_region: str = "us-east-1"
    # Make uploaded images public without moderation. Moderation is not built yet.
    media_auto_approve: bool = False
    # Listing modes switched off for launch: new listings can't use them and
    # existing ones are hidden from search. Set to [] (JSON) to turn them back on.
    disabled_listing_modes: list[str] = ["lend", "rent", "request"]
    object_storage_secret_key: SecretStr = SecretStr(_DEV_STORAGE_SECRET)
    otel_enabled: bool = False
    password_reset_token_minutes: int = 30
    # Forgot-password requests per 15 minutes: per email address, and per client IP.
    auth_rate_limit_enabled: bool = True
    # Header the hosting proxy sets to the caller's address, overwriting anything the client
    # sent (Fly: "Fly-Client-IP"). Unset means trust the TCP peer address only.
    client_ip_header: str | None = None
    password_reset_per_email: int = 3
    password_reset_per_ip: int = 10
    # Failed sign-ins per 15 minutes before further tries are refused; sign-ups per hour per IP.
    login_failures_per_email: int = 10
    login_failures_per_ip: int = 50
    registrations_per_ip: int = 10
    redis_url: str = "redis://localhost:6379/0"
    max_request_body_bytes: int = 1_000_000  # JSON only; photos upload to storage directly
    # Background jobs (worker.py): how long each kind of hold lasts before it is released.
    unpaid_order_minutes: int = 60  # an unpaid checkout keeps its copies this long
    offer_hold_hours: int = 72  # an accepted offer with no pickup or payment arranged
    buyer_protection_days: int = 3  # after delivery, before the order completes on its own
    worker_interval_seconds: int = 60
    refresh_token_expire_days: int = 30
    request_id_header: str = "X-Request-ID"

    # Location / geo
    geoip_mmdb_path: str | None = (
        None  # Path to GeoLite2-City.mmdb; if unset IP detection is skipped.
    )
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "OldPages.in (contact@oldpages.in)"
    nominatim_timeout_seconds: float = 5.0
    geo_cache_ttl_seconds: int = 7 * 24 * 3600
    geo_default_radius_km: float = 25.0
    geo_max_radius_km: float = 500.0
    geo_active_cookie_name: str = "op_loc"
    geo_active_cookie_max_age_days: int = 90

    @model_validator(mode="after")
    def refuse_unsafe_defaults(self) -> Settings:
        """A deployed API must not run on development secrets or development shortcuts."""
        if self.environment not in {"staging", "production"}:
            return self
        problems = []
        jwt_secret = self.jwt_secret_key.get_secret_value()
        if jwt_secret == _DEV_JWT_SECRET or len(jwt_secret) < 32:
            problems.append(
                "OLDPAGES_JWT_SECRET_KEY must be set to a random value of 32+ characters"
            )
        if self.object_storage_secret_key.get_secret_value() == _DEV_STORAGE_SECRET:
            problems.append("OLDPAGES_OBJECT_STORAGE_SECRET_KEY must be set")
        if self.expose_development_auth_tokens:
            problems.append("OLDPAGES_EXPOSE_DEVELOPMENT_AUTH_TOKENS must be false")
        if not self.public_web_url.startswith("https://"):
            problems.append("OLDPAGES_PUBLIC_WEB_URL must be the https:// site address")
        if problems:
            raise ValueError(f"Unsafe {self.environment} settings: " + "; ".join(problems))
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
