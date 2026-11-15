from __future__ import annotations

import io
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, cast

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from oldpages_api.business import models as _business_models  # noqa: F401
from oldpages_api.catalog import models as _catalog_models  # noqa: F401
from oldpages_api.chat import models as _chat_models  # noqa: F401
from oldpages_api.clubs import models as _club_models  # noqa: F401
from oldpages_api.commerce import models as _commerce_models  # noqa: F401
from oldpages_api.communities import models as _community_models  # noqa: F401
from oldpages_api.core.config import Settings
from oldpages_api.donations import models as _donation_models  # noqa: F401
from oldpages_api.identity import models as _identity_models  # noqa: F401
from oldpages_api.institutions import models as _institution_models  # noqa: F401
from oldpages_api.listings import models as _listing_models  # noqa: F401
from oldpages_api.main import create_app
from oldpages_api.notifications import models as _notification_models  # noqa: F401
from oldpages_api.payments import models as _payment_models  # noqa: F401
from oldpages_api.reading import models as _reading_models  # noqa: F401
from oldpages_api.recommendations import models as _recommendation_models  # noqa: F401
from oldpages_api.search import models as _search_models  # noqa: F401
from oldpages_api.shared.db.base import Base
from oldpages_api.shared.db.database import get_session
from oldpages_api.subscriptions import models as _subscription_models  # noqa: F401
from oldpages_api.trust import models as _trust_models  # noqa: F401

RegisterUser = Callable[..., Awaitable[dict[str, Any]]]


def sample_jpeg() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(out, "JPEG")
    return out.getvalue()


@pytest.fixture(autouse=True)
def stub_object_storage(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    """Tests have no MinIO: keep objects in a dict; a completed upload is a small JPEG."""
    stored: dict[str, bytes] = {}

    async def _read(settings: Settings, storage_key: str, *, max_bytes: int) -> bytes | None:
        data = stored.get(storage_key, sample_jpeg())
        if len(data) > max_bytes:
            raise ValueError("object too large")
        return data

    async def _write(settings: Settings, storage_key: str, data: bytes, content_type: str) -> None:
        stored[storage_key] = data

    async def _delete(settings: Settings, storage_key: str) -> None:
        stored.pop(storage_key, None)

    monkeypatch.setattr("oldpages_api.listings.service.read_object", _read)
    monkeypatch.setattr("oldpages_api.listings.service.write_object", _write)
    monkeypatch.setattr("oldpages_api.listings.service.delete_object", _delete)
    return stored


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment="test",
        expose_development_auth_tokens=True,
        auth_rate_limit_enabled=False,
        jwt_secret_key=SecretStr("test-secret-key-that-is-at-least-32-bytes"),
        otel_enabled=False,
    )


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=db_engine, expire_on_commit=False)


@pytest.fixture
async def client(
    test_settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    app = create_app(test_settings)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def register_user() -> RegisterUser:
    async def _register_user(
        client: AsyncClient,
        *,
        email: str = "reader@example.com",
        display_name: str = "Reader",
        password: str = "correct horse battery staple",  # noqa: S107
        username: str | None = "reader",
    ) -> dict[str, Any]:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "display_name": display_name,
                "email": email,
                "password": password,
                "privacy_accepted": True,
                "terms_accepted": True,
                "username": username,
            },
        )
        assert response.status_code == 201, response.text
        return cast("dict[str, Any]", response.json())

    return _register_user
