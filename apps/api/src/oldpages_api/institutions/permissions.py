from __future__ import annotations

from oldpages_api.identity.models import User
from oldpages_api.institutions.exceptions import ForbiddenInstitutionActionError
from oldpages_api.institutions.models import Institution, InstitutionMember


def require_institution_admin(
    institution: Institution,
    user: User,
    member_map: dict[int, InstitutionMember],
) -> None:
    member = member_map.get(user.id)
    is_owner = institution.owner_user_id == user.id
    is_admin = member is not None and member.role == "admin" and member.status == "active"
    if not is_owner and not is_admin:
        raise ForbiddenInstitutionActionError("Only institution admins can perform this action.")


def require_institution_member(
    institution_id: int,
    user_id: int,
    member_map: dict[int, InstitutionMember],
) -> None:
    member = member_map.get(user_id)
    if member is None or member.institution_id != institution_id or member.status != "active":
        raise ForbiddenInstitutionActionError(
            "Only active institution members can perform this action."
        )
