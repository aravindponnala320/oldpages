from __future__ import annotations

import re
from collections import Counter
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.communities.events import (
    COMMUNITY_COMMENT_CREATED,
    COMMUNITY_CREATED,
    COMMUNITY_JOIN_REQUESTED,
    COMMUNITY_MEMBER_APPROVED,
    COMMUNITY_POST_CREATED,
    COMMUNITY_REACTION_SET,
    COMMUNITY_REPORT_CREATED,
)
from oldpages_api.communities.exceptions import (
    CommunityNotFoundError,
    CommunityPostNotFoundError,
    CommunityValidationError,
    ForbiddenCommunityActionError,
    InvalidCommunityStateTransitionError,
)
from oldpages_api.communities.models import (
    Community,
    CommunityChannel,
    CommunityMember,
    CommunityPost,
    CommunityReport,
    CommunityRole,
    CommunityRule,
    PostComment,
    PostReaction,
)
from oldpages_api.communities.permissions import (
    member_for,
    require_active_member,
    require_can_view,
    require_moderator,
)
from oldpages_api.communities.repository import CommunityRepository
from oldpages_api.communities.schemas import (
    CommunityApproveMemberRequest,
    CommunityChannelResponse,
    CommunityChannelType,
    CommunityChannelVisibility,
    CommunityCreateRequest,
    CommunityFeedResponse,
    CommunityJoinRequest,
    CommunityListResponse,
    CommunityMarketplaceResponse,
    CommunityMemberResponse,
    CommunityMembershipPolicy,
    CommunityMemberStatus,
    CommunityPostCreateRequest,
    CommunityPostResponse,
    CommunityPostStatus,
    CommunityPostType,
    CommunityReportCreateRequest,
    CommunityReportResponse,
    CommunityReportStatus,
    CommunityReportTargetType,
    CommunityResponse,
    CommunityRuleResponse,
    CommunitySummaryResponse,
    CommunityType,
    CommunityUserSummary,
    CommunityVisibility,
    PostCommentCreateRequest,
    PostCommentResponse,
    PostReactionRequest,
    PostReactionResponse,
    PostReactionType,
)
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.listings.service import listing_response

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class CommunityService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CommunityRepository(session)

    async def create_community(
        self,
        payload: CommunityCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> CommunityResponse:
        book_edition = None
        if payload.book_id is not None:
            book_edition = await self.repo.get_book_edition_by_public_id(payload.book_id)
            if book_edition is None:
                raise CommunityValidationError("Book scope was not found.")
        slug = slugify(payload.slug or payload.name)
        existing = await self.repo.get_community_by_slug(slug)
        if existing is not None:
            raise CommunityValidationError("Community slug is already in use.")
        membership_policy = payload.membership_policy or default_membership_policy(
            payload.visibility
        )
        if membership_policy == "institution_verified" and not payload.institution:
            raise CommunityValidationError(
                "Institution-verified communities require an institution."
            )
        community = Community(
            book_edition_id=book_edition.id if book_edition is not None else None,
            city=payload.city,
            community_type=payload.community_type,
            country=payload.country,
            cover_image_url=payload.cover_image_url,
            description=payload.description,
            genre=payload.genre,
            institution=payload.institution,
            language=payload.language,
            membership_policy=membership_policy,
            name=payload.name,
            owner_user_id=actor.id,
            settings_json=payload.settings,
            slug=slug,
            state=payload.state,
            visibility=payload.visibility,
        )
        self.repo.add(community)
        await self.repo.flush()

        owner_role = CommunityRole(
            community_id=community.id,
            is_default=False,
            name="owner",
            permissions_json=["manage", "moderate", "post", "approve_member"],
            sort_order=0,
        )
        moderator_role = CommunityRole(
            community_id=community.id,
            is_default=False,
            name="moderator",
            permissions_json=["moderate", "post", "approve_member"],
            sort_order=1,
        )
        member_role = CommunityRole(
            community_id=community.id,
            is_default=True,
            name="member",
            permissions_json=["post", "comment", "react"],
            sort_order=2,
        )
        self.repo.add(owner_role)
        self.repo.add(moderator_role)
        self.repo.add(member_role)
        await self.repo.flush()

        now = utc_now()
        self.repo.add(
            CommunityMember(
                approved_at=now,
                community_id=community.id,
                joined_at=now,
                requested_at=now,
                role_id=owner_role.id,
                status="active",
                user_id=actor.id,
            )
        )
        rules = [(rule.title, rule.body) for rule in payload.rules] or [
            ("Be useful", "Keep posts relevant to this community.")
        ]
        for index, (title, body) in enumerate(rules):
            self.repo.add(
                CommunityRule(
                    body=body,
                    community_id=community.id,
                    sort_order=index,
                    title=title,
                )
            )
        channels = [
            (channel.name, channel.channel_type, channel.slug or channel.name, channel.visibility)
            for channel in payload.channels
        ] or [
            ("General", "general", "general", "members"),
            ("Marketplace", "marketplace", "marketplace", "members"),
        ]
        for index, (name, channel_type, channel_slug, visibility) in enumerate(channels):
            self.repo.add(
                CommunityChannel(
                    channel_type=channel_type,
                    community_id=community.id,
                    name=name,
                    slug=slugify(channel_slug),
                    sort_order=index,
                    visibility=visibility,
                )
            )
        await self.audit(
            action=COMMUNITY_CREATED,
            actor=actor,
            context=context,
            payload={"community_id": community.public_id, "visibility": community.visibility},
        )
        await self.repo.commit()
        reloaded = await self.get_community_model(community.public_id)
        return await self.community_response(reloaded, actor)

    async def list_communities(
        self,
        *,
        book_id: str | None,
        city: str | None,
        country: str | None,
        cursor: str | None,
        genre: str | None,
        institution: str | None,
        limit: int,
        viewer: User | None,
    ) -> CommunityListResponse:
        communities, next_cursor = await self.repo.list_communities(
            book_id=book_id,
            city=city,
            country=country,
            cursor=cursor,
            genre=genre,
            institution=institution,
            limit=limit,
        )
        return CommunityListResponse(
            items=[
                await self.community_summary_response(community, viewer)
                for community in communities
            ],
            next_cursor=next_cursor,
        )

    async def get_community(
        self,
        community_id: str,
        viewer: User | None,
    ) -> CommunityResponse:
        community = await self.get_community_model(community_id)
        require_can_view(viewer, community)
        return await self.community_response(community, viewer)

    async def join_community(
        self,
        community_id: str,
        payload: CommunityJoinRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> CommunityMemberResponse:
        community = await self.get_community_model(community_id)
        existing = await self.repo.get_member(community.id, actor.id)
        if existing is not None and existing.status in {"active", "pending"}:
            return member_response(existing)
        if existing is not None and existing.status in {"banned", "muted"}:
            raise ForbiddenCommunityActionError("This membership is not eligible to join.")

        role = await self.require_role(community.id, "member")
        now = utc_now()
        status_value = await self.join_status_for(community, actor)
        if existing is None:
            member = CommunityMember(
                answers_json=payload.answers,
                community_id=community.id,
                requested_at=now,
                role_id=role.id,
                status=status_value,
                user_id=actor.id,
            )
            self.repo.add(member)
        else:
            member = existing
            member.answers_json = payload.answers
            member.requested_at = now
            member.role_id = role.id
            member.status = status_value
        if status_value == "active":
            member.approved_at = now
            member.joined_at = now
        await self.audit(
            action=COMMUNITY_JOIN_REQUESTED,
            actor=actor,
            context=context,
            payload={"community_id": community.public_id, "status": status_value},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_member(community.id, actor.id)
        if reloaded is None:
            raise CommunityValidationError("Membership could not be created.")
        return member_response(reloaded)

    async def approve_member(
        self,
        community_id: str,
        payload: CommunityApproveMemberRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> CommunityMemberResponse:
        community = await self.get_community_model(community_id)
        require_moderator(actor, community)
        target = await self.repo.get_user_by_public_id(payload.user_id)
        if target is None:
            raise CommunityValidationError("User was not found.")
        member = await self.repo.get_member(community.id, target.id)
        if member is None:
            raise CommunityValidationError("User has not requested membership.")
        if member.status == "banned":
            raise InvalidCommunityStateTransitionError("Banned members cannot be approved.")
        role = await self.require_role(community.id, payload.role)
        now = utc_now()
        member.approved_at = now
        member.joined_at = member.joined_at or now
        member.role_id = role.id
        member.status = "active"
        await self.audit(
            action=COMMUNITY_MEMBER_APPROVED,
            actor=actor,
            context=context,
            payload={
                "community_id": community.public_id,
                "role": payload.role,
                "user_id": target.public_id,
            },
        )
        await self.repo.commit()
        reloaded = await self.repo.get_member(community.id, target.id)
        if reloaded is None:
            raise CommunityValidationError("Membership could not be loaded.")
        return member_response(reloaded)

    async def create_post(
        self,
        community_id: str,
        payload: CommunityPostCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> CommunityPostResponse:
        community = await self.get_community_model(community_id)
        require_active_member(actor, community)
        channel_id = None
        if payload.channel_id:
            channel = await self.repo.get_channel_by_public_id(payload.channel_id)
            if channel is None or channel.community_id != community.id:
                raise CommunityValidationError("Channel was not found in this community.")
            channel_id = channel.id
        listing_id = None
        if payload.listing_id:
            listing = await self.repo.get_listing_by_public_id(payload.listing_id)
            if listing is None:
                raise CommunityValidationError("Listing was not found.")
            listing_id = listing.id
        if payload.is_pinned or payload.is_announcement:
            require_moderator(actor, community)
        post = CommunityPost(
            author_user_id=actor.id,
            body=payload.body,
            channel_id=channel_id,
            community_id=community.id,
            is_announcement=payload.is_announcement,
            is_pinned=payload.is_pinned,
            listing_id=listing_id,
            poll_json={"options": payload.poll_options} if payload.post_type == "poll" else {},
            post_type=payload.post_type,
            status="published",
            title=payload.title,
        )
        self.repo.add(post)
        await self.audit(
            action=COMMUNITY_POST_CREATED,
            actor=actor,
            context=context,
            payload={"community_id": community.public_id, "post_type": payload.post_type},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_post_by_public_id(post.public_id)
        if reloaded is None:
            raise CommunityPostNotFoundError()
        return post_response(reloaded, actor)

    async def get_feed(
        self,
        community_id: str,
        *,
        cursor: str | None,
        limit: int,
        viewer: User | None,
    ) -> CommunityFeedResponse:
        community = await self.get_community_model(community_id)
        require_can_view(viewer, community)
        posts, next_cursor = await self.repo.list_feed(
            community.id,
            cursor=cursor,
            limit=limit,
        )
        return CommunityFeedResponse(
            items=[post_response(post, viewer) for post in posts],
            next_cursor=next_cursor,
        )

    async def create_comment(
        self,
        post_id: str,
        payload: PostCommentCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> PostCommentResponse:
        post = await self.repo.get_post_by_public_id(post_id)
        if post is None:
            raise CommunityPostNotFoundError()
        require_active_member(actor, post.community)
        parent_id = None
        if payload.parent_comment_id:
            parent = await self.repo.get_comment_by_public_id(payload.parent_comment_id)
            if parent is None or parent.post_id != post.id:
                raise CommunityValidationError("Parent comment was not found for this post.")
            parent_id = parent.id
        comment = PostComment(
            author_user_id=actor.id,
            body=payload.body,
            parent_comment_id=parent_id,
            post_id=post.id,
        )
        self.repo.add(comment)
        await self.audit(
            action=COMMUNITY_COMMENT_CREATED,
            actor=actor,
            context=context,
            payload={"community_id": post.community.public_id, "post_id": post.public_id},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_comment_by_public_id(comment.public_id)
        if reloaded is None:
            raise CommunityValidationError("Comment could not be created.")
        return comment_response(reloaded)

    async def set_reaction(
        self,
        post_id: str,
        payload: PostReactionRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> PostReactionResponse:
        post = await self.repo.get_post_by_public_id(post_id)
        if post is None:
            raise CommunityPostNotFoundError()
        require_active_member(actor, post.community)
        reaction = await self.repo.get_reaction(post.id, actor.id)
        if reaction is None:
            reaction = PostReaction(
                post_id=post.id,
                reaction_type=payload.reaction_type,
                user_id=actor.id,
            )
            self.repo.add(reaction)
        else:
            reaction.reaction_type = payload.reaction_type
        await self.audit(
            action=COMMUNITY_REACTION_SET,
            actor=actor,
            context=context,
            payload={
                "community_id": post.community.public_id,
                "post_id": post.public_id,
                "reaction_type": payload.reaction_type,
            },
        )
        await self.repo.commit()
        return PostReactionResponse(
            id=reaction.public_id,
            post_id=post.public_id,
            reaction_type=cast("PostReactionType", reaction.reaction_type),
            user_id=actor.public_id,
        )

    async def marketplace(
        self,
        community_id: str,
        *,
        cursor: str | None,
        limit: int,
        viewer: User | None,
    ) -> CommunityMarketplaceResponse:
        community = await self.get_community_model(community_id)
        require_can_view(viewer, community)
        listings, next_cursor = await self.repo.list_marketplace(
            community,
            cursor=cursor,
            limit=limit,
        )
        return CommunityMarketplaceResponse(
            community_id=community.public_id,
            items=[listing_response(listing) for listing in listings],
            next_cursor=next_cursor,
        )

    async def create_report(
        self,
        community_id: str,
        payload: CommunityReportCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> CommunityReportResponse:
        community = await self.get_community_model(community_id)
        require_can_view(actor, community)
        report = CommunityReport(
            community_id=community.id,
            details=payload.details,
            reason=payload.reason,
            reporter_user_id=actor.id,
            target_type=payload.target_type,
        )
        if payload.target_type == "post" and payload.target_id:
            post = await self.repo.get_post_by_public_id(payload.target_id)
            if post is None or post.community_id != community.id:
                raise CommunityValidationError("Reported post was not found.")
            report.target_community_post_id = post.id
        elif payload.target_type == "comment" and payload.target_id:
            comment = await self.repo.get_comment_by_public_id(payload.target_id)
            if comment is None:
                raise CommunityValidationError("Reported comment was not found.")
            if comment.post.community_id != community.id:
                raise CommunityValidationError("Reported comment was not found.")
            report.target_post_comment_id = comment.id
        elif payload.target_type == "member" and payload.target_id:
            user = await self.repo.get_user_by_public_id(payload.target_id)
            if user is None:
                raise CommunityValidationError("Reported member was not found.")
            member = await self.repo.get_member(community.id, user.id)
            if member is None:
                raise CommunityValidationError("Reported member was not found.")
            report.target_member_user_id = user.id
        self.repo.add(report)
        await self.audit(
            action=COMMUNITY_REPORT_CREATED,
            actor=actor,
            context=context,
            payload={"community_id": community.public_id, "target_type": payload.target_type},
        )
        await self.repo.commit()
        return report_response(report, community.public_id, payload.target_id)

    async def get_community_model(self, community_id: str) -> Community:
        community = await self.repo.get_community_by_public_id(community_id)
        if community is None:
            raise CommunityNotFoundError()
        return community

    async def require_role(self, community_id: int, name: str) -> CommunityRole:
        role = await self.repo.get_role(community_id, name)
        if role is None:
            raise CommunityValidationError(f"Community role {name!r} is not configured.")
        return role

    async def join_status_for(self, community: Community, actor: User) -> str:
        if community.membership_policy == "open":
            return "active"
        if community.membership_policy == "institution_verified":
            profile = await self.repo.get_profile_by_user_id(actor.id)
            if profile is None or not profile.institution:
                raise ForbiddenCommunityActionError("A verified institution is required to join.")
            if (
                not community.institution
                or profile.institution.lower() != community.institution.lower()
            ):
                raise ForbiddenCommunityActionError("This institution membership is not eligible.")
            return "active"
        return "pending"

    async def community_summary_response(
        self,
        community: Community,
        viewer: User | None,
    ) -> CommunitySummaryResponse:
        member = member_for(viewer, community)
        return CommunitySummaryResponse(
            book_id=community.book_edition.public_id if community.book_edition else None,
            city=community.city,
            community_type=cast("CommunityType", community.community_type),
            country=community.country,
            description=community.description,
            genre=community.genre,
            id=community.public_id,
            institution=community.institution,
            member_count=await self.repo.member_count(community.id),
            name=community.name,
            slug=community.slug,
            state=community.state,
            viewer_membership_status=cast("CommunityMemberStatus", member.status)
            if member
            else None,
            visibility=cast("CommunityVisibility", community.visibility),
        )

    async def community_response(
        self,
        community: Community,
        viewer: User | None,
    ) -> CommunityResponse:
        summary = await self.community_summary_response(community, viewer)
        return CommunityResponse(
            **summary.model_dump(),
            channels=[
                channel_response(channel)
                for channel in sorted(community.channels, key=lambda item: item.sort_order)
            ],
            membership_policy=cast("CommunityMembershipPolicy", community.membership_policy),
            owner=CommunityUserSummary(id=community.owner.public_id),
            rules=[
                rule_response(rule)
                for rule in sorted(community.rules, key=lambda item: item.sort_order)
                if rule.enabled
            ],
        )

    async def audit(
        self,
        *,
        action: str,
        actor: User,
        context: AuthenticatedRequestContext,
        payload: dict[str, Any],
    ) -> None:
        self.repo.add(
            AuditLog(
                action=action,
                actor_user_id=actor.id,
                context_json=payload,
                ip_address=context.ip_address,
                target_user_id=None,
                user_agent=context.user_agent,
            )
        )


def default_membership_policy(visibility: str) -> str:
    if visibility == "public":
        return "open"
    if visibility == "institution_verified":
        return "institution_verified"
    return "approval"


def slugify(value: str) -> str:
    slug = _SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
    if not slug:
        raise CommunityValidationError("Community slug cannot be empty.")
    return slug[:140]


def channel_response(channel: CommunityChannel) -> CommunityChannelResponse:
    return CommunityChannelResponse(
        channel_type=cast("CommunityChannelType", channel.channel_type),
        id=channel.public_id,
        name=channel.name,
        slug=channel.slug,
        visibility=cast("CommunityChannelVisibility", channel.visibility),
    )


def rule_response(rule: CommunityRule) -> CommunityRuleResponse:
    return CommunityRuleResponse(
        body=rule.body,
        enabled=rule.enabled,
        id=rule.public_id,
        sort_order=rule.sort_order,
        title=rule.title,
    )


def member_response(member: CommunityMember) -> CommunityMemberResponse:
    return CommunityMemberResponse(
        joined_at=member.joined_at,
        role=member.role.name,
        status=cast("CommunityMemberStatus", member.status),
        user=CommunityUserSummary(id=member.user.public_id),
    )


def post_response(post: CommunityPost, viewer: User | None) -> CommunityPostResponse:
    reaction_counts = Counter(reaction.reaction_type for reaction in post.reactions)
    viewer_reaction = next(
        (
            reaction.reaction_type
            for reaction in post.reactions
            if viewer is not None and reaction.user_id == viewer.id
        ),
        None,
    )
    return CommunityPostResponse(
        author=CommunityUserSummary(id=post.author.public_id),
        body=post.body,
        channel_id=post.channel.public_id if post.channel else None,
        comment_count=len([comment for comment in post.comments if comment.status == "published"]),
        community_id=post.community.public_id,
        created_at=post.created_at,
        id=post.public_id,
        is_announcement=post.is_announcement,
        is_pinned=post.is_pinned,
        listing_id=post.listing.public_id if post.listing else None,
        poll=post.poll_json,
        post_type=cast("CommunityPostType", post.post_type),
        reaction_counts=dict(reaction_counts),
        status=cast("CommunityPostStatus", post.status),
        title=post.title,
        viewer_reaction=cast("PostReactionType | None", viewer_reaction),
    )


def comment_response(comment: PostComment) -> PostCommentResponse:
    return PostCommentResponse(
        author=CommunityUserSummary(id=comment.author.public_id),
        body=comment.body,
        created_at=comment.created_at,
        id=comment.public_id,
        parent_comment_id=comment.parent.public_id if comment.parent else None,
        post_id=comment.post.public_id,
        status=comment.status,
    )


def report_response(
    report: CommunityReport,
    community_public_id: str,
    target_public_id: str | None,
) -> CommunityReportResponse:
    return CommunityReportResponse(
        community_id=community_public_id,
        created_at=report.created_at,
        id=report.public_id,
        reason=report.reason,
        status=cast("CommunityReportStatus", report.status),
        target_id=target_public_id,
        target_type=cast("CommunityReportTargetType", report.target_type),
    )
