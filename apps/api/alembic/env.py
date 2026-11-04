from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from oldpages_api.catalog import models as _catalog_models  # noqa: F401
from oldpages_api.chat import models as _chat_models  # noqa: F401
from oldpages_api.clubs import models as _club_models  # noqa: F401
from oldpages_api.commerce import models as _commerce_models  # noqa: F401
from oldpages_api.communities import models as _community_models  # noqa: F401
from oldpages_api.core.config import get_settings
from oldpages_api.identity import models as _identity_models  # noqa: F401
from oldpages_api.listings import models as _listing_models  # noqa: F401
from oldpages_api.notifications import models as _notification_models  # noqa: F401
from oldpages_api.reading import models as _reading_models  # noqa: F401
from oldpages_api.search import models as _search_models  # noqa: F401
from oldpages_api.shared.db.base import Base
from oldpages_api.shared.events import models as _outbox_models  # noqa: F401
from oldpages_api.trust import models as _trust_models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        compare_type=True,
        literal_binds=True,
        target_metadata=target_metadata,
        url=database_url(),
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        compare_type=True,
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = database_url()
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
