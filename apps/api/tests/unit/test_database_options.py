from __future__ import annotations

import pytest

from oldpages_api.core.config import get_settings
from oldpages_api.shared.db.database import engine_options


def test_postgres_connections_cap_query_time_and_pool_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLDPAGES_DATABASE_URL", "postgresql+asyncpg://u:p@db/oldpages")
    monkeypatch.setenv("OLDPAGES_DATABASE_STATEMENT_TIMEOUT_MS", "3000")
    get_settings.cache_clear()
    try:
        options = engine_options()
    finally:
        get_settings.cache_clear()

    assert options["pool_size"] == 5
    assert options["max_overflow"] == 10
    assert options["connect_args"]["server_settings"]["statement_timeout"] == "3000"
