from __future__ import annotations

from oldpages_api.core.config import Settings


def test_settings_parse_cors_origins_from_comma_separated_string() -> None:
    settings = Settings.model_validate(
        {"cors_origins": "http://localhost:3000, http://localhost:3001"}
    )

    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:3001"]
