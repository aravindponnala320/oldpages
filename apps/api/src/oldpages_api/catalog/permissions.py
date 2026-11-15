from __future__ import annotations

from oldpages_api.catalog.exceptions import ForbiddenCatalogActionError
from oldpages_api.identity.models import User

# Books are shared by every listing of that edition, so only these roles may correct them.
CATALOG_EDITOR_ROLES = ("admin", "moderator", "catalog_manager")


def require_catalog_manager(user: User) -> None:
    if user.status != "active":
        raise ForbiddenCatalogActionError()


def require_catalog_editor(user: User, has_editor_role: bool) -> None:
    require_catalog_manager(user)
    if not has_editor_role:
        raise ForbiddenCatalogActionError()
