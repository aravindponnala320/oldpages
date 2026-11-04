from __future__ import annotations

from oldpages_api.business.exceptions import ForbiddenBusinessActionError
from oldpages_api.business.models import BusinessProfile, StaffAccount
from oldpages_api.identity.models import User


def require_business_owner(profile: BusinessProfile, user: User) -> None:
    if profile.owner_user_id != user.id:
        raise ForbiddenBusinessActionError("Only the business owner can perform this action.")


def require_business_permission(
    profile: BusinessProfile,
    user: User,
    permission: str,
) -> StaffAccount:
    if profile.owner_user_id == user.id:
        owner_staff = next(
            (
                staff
                for staff in profile.staff_accounts
                if staff.user_id == user.id and staff.status == "active"
            ),
            None,
        )
        if owner_staff is not None:
            return owner_staff
        raise ForbiddenBusinessActionError("Business owner staff account is not active.")
    staff = next(
        (
            staff
            for staff in profile.staff_accounts
            if staff.user_id == user.id and staff.status == "active"
        ),
        None,
    )
    if staff is None:
        raise ForbiddenBusinessActionError(
            "Only staff members of this business can perform this action."
        )
    if permission not in staff.permissions_json:
        raise ForbiddenBusinessActionError("Staff account is missing the required permission.")
    return staff


def require_business_staff(
    profile_id: int,
    user_id: int,
    staff_map: dict[int, StaffAccount],
) -> StaffAccount:
    staff = staff_map.get(user_id)
    if staff is None or staff.business_profile_id != profile_id:
        raise ForbiddenBusinessActionError(
            "Only staff members of this business can perform this action."
        )
    if staff.status != "active":
        raise ForbiddenBusinessActionError("Staff account is not active.")
    return staff
