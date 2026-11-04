from __future__ import annotations

from oldpages_api.catalog.exceptions import ForbiddenCatalogActionError
from oldpages_api.identity.models import User


def require_catalog_manager(user: User) -> None:
    if user.status != "active":
        raise ForbiddenCatalogActionError()
