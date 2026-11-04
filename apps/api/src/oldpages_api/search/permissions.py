from __future__ import annotations

from oldpages_api.identity.models import User
from oldpages_api.search.exceptions import ForbiddenSearchActionError


def require_owner(actor: User, owner_user_id: int) -> None:
    if actor.id != owner_user_id:
        raise ForbiddenSearchActionError()
