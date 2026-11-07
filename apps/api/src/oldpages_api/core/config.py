from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    debug: bool = False
    environment: Literal["local", "test", "staging", "production"] = "local"
    email_verification_token_hours: int = 24
    email_provider: Literal["resend", "noop"] = "noop"
    email_from: str = "OldPages <noreply@oldpages.in>"
    resend_api_key: SecretStr | None = None
    public_web_url: str = "http://localhost:3000"
    google_client_id: str | None = None
    expose_development_auth_tokens: bool = True
    jwt_algorithm: str = "HS256"
    jwt_secret_key: SecretStr = SecretStr("development-only-change-me")
    log_level: str = "INFO"
    object_storage_access_key: str = "oldpages"
    object_storage_bucket: str = "oldpages-media"
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_secret_key: SecretStr = SecretStr("oldpages-secret")
    otel_enabled: bool = False
    password_reset_token_minutes: int = 30
    redis_url: str = "redis://localhost:6379/0"
    refresh_token_expire_days: int = 30
    request_id_header: str = "X-Request-ID"

    # Location / geo
    geoip_mmdb_path: str | None = None  # Path to GeoLite2-City.mmdb; if unset IP detection is skipped.
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "OldPages.in (contact@oldpages.in)"
    nominatim_timeout_seconds: float = 5.0
    geo_cache_ttl_seconds: int = 7 * 24 * 3600
    geo_default_radius_km: float = 25.0
    geo_max_radius_km: float = 500.0
    geo_active_cookie_name: str = "op_loc"
    geo_active_cookie_max_age_days: int = 90

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
