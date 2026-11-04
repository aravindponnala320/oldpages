from __future__ import annotations

from oldpages_api.communities.exceptions import ForbiddenCommunityActionError
from oldpages_api.communities.models import Community, CommunityMember
from oldpages_api.identity.models import User


def active_member_for(user: User | None, community: Community) -> CommunityMember | None:
    if user is None:
        return None
    return next(
        (
            member
            for member in community.members
            if member.user_id == user.id and member.status == "active"
        ),
        None,
    )


def member_for(user: User | None, community: Community) -> CommunityMember | None:
    if user is None:
        return None
    return next(
        (member for member in community.members if member.user_id == user.id),
        None,
    )


def can_view_community(user: User | None, community: Community) -> bool:
    if community.visibility == "public":
        return True
    return active_member_for(user, community) is not None


def is_moderator_member(member: CommunityMember | None) -> bool:
    if member is None:
        return False
    permissions = member.role.permissions_json
    return member.role.name in {"owner", "moderator"} or "moderate" in permissions


def require_can_view(user: User | None, community: Community) -> None:
    if not can_view_community(user, community):
        raise ForbiddenCommunityActionError("Community content is available to members only.")


def require_active_member(user: User, community: Community) -> CommunityMember:
    member = active_member_for(user, community)
    if member is None:
        raise ForbiddenCommunityActionError("This community action requires active membership.")
    return member


def require_moderator(user: User, community: Community) -> CommunityMember:
    member = active_member_for(user, community)
    if member is None or not is_moderator_member(member):
        raise ForbiddenCommunityActionError("Only community moderators can perform this action.")
    return member
