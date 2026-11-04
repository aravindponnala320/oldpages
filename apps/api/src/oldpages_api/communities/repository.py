from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.catalog.models import BookEdition
from oldpages_api.communities.models import (
    Community,
    CommunityChannel,
    CommunityMember,
    CommunityPost,
    CommunityRole,
    PostComment,
    PostReaction,
)
from oldpages_api.identity.models import User, UserProfile
from oldpages_api.listings.models import Listing, ListingLocation
from oldpages_api.listings.repository import listing_load_options


class CommunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_book_edition_by_public_id(self, public_id: str) -> BookEdition | None:
        result = await self.session.execute(
            select(BookEdition).where(BookEdition.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        result = await self.session.execute(
            select(User).options(selectinload(User.profile)).where(User.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_user_id(self, user_id: int) -> UserProfile | None:
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_listing_by_public_id(self, public_id: str) -> Listing | None:
        result = await self.session.execute(
            select(Listing).options(*listing_load_options()).where(Listing.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_community_by_public_id(self, public_id: str) -> Community | None:
        result = await self.session.execute(
            select(Community)
            .execution_options(populate_existing=True)
            .options(*community_load_options())
            .where(Community.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_community_by_slug(self, slug: str) -> Community | None:
        result = await self.session.execute(
            select(Community).options(*community_load_options()).where(Community.slug == slug)
        )
        return result.unique().scalar_one_or_none()

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
    ) -> tuple[list[Community], str | None]:
        stmt = (
            select(Community)
            .options(*community_load_options())
            .where(Community.status == "active", Community.visibility != "secret")
            .order_by(Community.created_at.desc(), Community.id.desc())
            .limit(limit + 1)
        )
        if city:
            stmt = stmt.where(func.lower(Community.city) == city.lower())
        if country:
            stmt = stmt.where(func.lower(Community.country) == country.lower())
        if institution:
            stmt = stmt.where(func.lower(Community.institution) == institution.lower())
        if genre:
            stmt = stmt.where(func.lower(Community.genre) == genre.lower())
        if book_id:
            book = await self.get_book_edition_by_public_id(book_id)
            if book is None:
                return [], None
            stmt = stmt.where(Community.book_edition_id == book.id)
        if cursor:
            cursor_community = await self.get_community_by_public_id(cursor)
            if cursor_community is not None:
                stmt = stmt.where(Community.id < cursor_community.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def get_member(self, community_id: int, user_id: int) -> CommunityMember | None:
        result = await self.session.execute(
            select(CommunityMember)
            .options(selectinload(CommunityMember.role), selectinload(CommunityMember.user))
            .where(
                CommunityMember.community_id == community_id,
                CommunityMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_role(self, community_id: int, name: str) -> CommunityRole | None:
        result = await self.session.execute(
            select(CommunityRole).where(
                CommunityRole.community_id == community_id,
                CommunityRole.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def get_channel_by_public_id(self, public_id: str) -> CommunityChannel | None:
        result = await self.session.execute(
            select(CommunityChannel).where(CommunityChannel.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_post_by_public_id(self, public_id: str) -> CommunityPost | None:
        result = await self.session.execute(
            select(CommunityPost)
            .execution_options(populate_existing=True)
            .options(*post_load_options())
            .where(CommunityPost.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_feed(
        self,
        community_id: int,
        *,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[CommunityPost], str | None]:
        stmt = (
            select(CommunityPost)
            .options(*post_load_options())
            .where(
                CommunityPost.community_id == community_id,
                CommunityPost.status == "published",
            )
            .order_by(
                CommunityPost.is_pinned.desc(),
                CommunityPost.created_at.desc(),
                CommunityPost.id.desc(),
            )
            .limit(limit + 1)
        )
        if cursor:
            cursor_post = await self.get_post_by_public_id(cursor)
            if cursor_post is not None:
                stmt = stmt.where(CommunityPost.id < cursor_post.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def get_comment_by_public_id(self, public_id: str) -> PostComment | None:
        result = await self.session.execute(
            select(PostComment)
            .options(selectinload(PostComment.author), selectinload(PostComment.post))
            .where(PostComment.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_reaction(self, post_id: int, user_id: int) -> PostReaction | None:
        result = await self.session.execute(
            select(PostReaction).where(
                PostReaction.post_id == post_id,
                PostReaction.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_marketplace(
        self,
        community: Community,
        *,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Listing], str | None]:
        stmt: Select[tuple[Listing]] = (
            select(Listing)
            .options(*listing_load_options())
            .where(Listing.status == "active")
            .order_by(Listing.created_at.desc(), Listing.id.desc())
            .limit(limit + 1)
        )
        if community.book_edition_id is not None:
            stmt = stmt.where(Listing.book_edition_id == community.book_edition_id)
        if community.city or community.state or community.country:
            stmt = stmt.join(ListingLocation)
            if community.city:
                stmt = stmt.where(func.lower(ListingLocation.city) == community.city.lower())
            if community.state:
                stmt = stmt.where(func.lower(ListingLocation.state) == community.state.lower())
            if community.country:
                stmt = stmt.where(func.lower(ListingLocation.country) == community.country.lower())
        if community.institution:
            stmt = stmt.join(UserProfile, UserProfile.user_id == Listing.seller_user_id).where(
                func.lower(UserProfile.institution) == community.institution.lower()
            )
        if cursor:
            cursor_listing = await self.get_listing_by_public_id(cursor)
            if cursor_listing is not None:
                stmt = stmt.where(Listing.id < cursor_listing.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def member_count(self, community_id: int) -> int:
        result = await self.session.execute(
            select(func.count(CommunityMember.id)).where(
                CommunityMember.community_id == community_id,
                CommunityMember.status == "active",
            )
        )
        return int(result.scalar_one())

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def community_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Community.book_edition),
        selectinload(Community.channels),
        selectinload(Community.members).selectinload(CommunityMember.role),
        selectinload(Community.members).selectinload(CommunityMember.user),
        selectinload(Community.owner),
        selectinload(Community.roles),
        selectinload(Community.rules),
    )


def post_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(CommunityPost.author),
        selectinload(CommunityPost.channel),
        selectinload(CommunityPost.comments).selectinload(PostComment.author),
        selectinload(CommunityPost.community)
        .selectinload(Community.members)
        .selectinload(CommunityMember.role),
        selectinload(CommunityPost.community).selectinload(Community.roles),
        selectinload(CommunityPost.community).selectinload(Community.owner),
        selectinload(CommunityPost.listing),
        selectinload(CommunityPost.reactions),
    )


__all__ = ["CommunityRepository"]
