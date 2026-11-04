from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.catalog.models import Category
from oldpages_api.catalog.repository import CatalogRepository
from oldpages_api.catalog.schemas import (
    AcademicMetadataInput,
    AuthorInput,
    BookCreateRequest,
    PublisherInput,
)
from oldpages_api.catalog.service import CatalogService
from oldpages_api.chat.models import ChatRequest
from oldpages_api.chat.schemas import (
    ChatRequestActionRequest,
    ChatRequestCreateRequest,
    MessageCreateRequest,
)
from oldpages_api.chat.service import ChatService
from oldpages_api.clubs.models import BookClub, ClubBook, Event, ReadingMilestone
from oldpages_api.clubs.schemas import (
    BookClubCreateRequest,
    ClubBookCreateRequest,
    EventCreateRequest,
    ReadingMilestoneCreateRequest,
)
from oldpages_api.clubs.service import ClubService
from oldpages_api.commerce.models import Offer as CommerceOffer
from oldpages_api.commerce.schemas import OfferCreateRequest
from oldpages_api.commerce.service import CommerceService
from oldpages_api.communities.models import Community
from oldpages_api.communities.schemas import CommunityCreateRequest
from oldpages_api.communities.service import CommunityService
from oldpages_api.core.config import get_settings
from oldpages_api.identity.models import User, UserPreference, UserProfile
from oldpages_api.identity.repository import IdentityRepository
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import hash_password, utc_now
from oldpages_api.listings.models import Listing, MediaAsset
from oldpages_api.listings.repository import ListingRepository
from oldpages_api.listings.schemas import (
    ListingConditionInput,
    ListingCreateRequest,
    ListingDeliveryMethodInput,
    ListingImageInput,
    ListingLocationInput,
)
from oldpages_api.listings.service import ListingService
from oldpages_api.reading.models import ReadingGoal, ReadingNote, ReadingProgress
from oldpages_api.reading.schemas import (
    ReadingGoalCreateRequest,
    ReadingNoteCreateRequest,
    ReadingProgressUpdateRequest,
    ReadingStatisticRecomputeRequest,
)
from oldpages_api.reading.service import ReadingService
from oldpages_api.shared.db.database import get_session_factory
from oldpages_api.shared.db.ids import new_ulid
from oldpages_api.trust.models import Report
from oldpages_api.trust.schemas import ReportCreateRequest
from oldpages_api.trust.service import TrustService

DEMO_PASSWORD = "OldPagesDemo!2026"  # noqa: S105


async def seed_identity(session: AsyncSession) -> User:
    repo = IdentityRepository(session)
    existing = await repo.get_user_by_email("demo@oldpages.in")
    if existing is not None:
        print("Seed user already exists: demo@oldpages.in")
        return existing

    user = User(
        email="demo@oldpages.in",
        email_verified_at=utc_now(),
        password_hash=hash_password(DEMO_PASSWORD),
        status="active",
    )
    repo.add(user)
    await repo.flush()
    repo.add(UserProfile(user_id=user.id, display_name="OldPages Demo", username="demo"))
    repo.add(UserPreference(user_id=user.id))
    await repo.commit()
    print("Created seed user: demo@oldpages.in / OldPagesDemo!2026")
    return user


async def seed_buyer_identity(session: AsyncSession) -> User:
    repo = IdentityRepository(session)
    existing = await repo.get_user_by_email("buyer@oldpages.in")
    if existing is not None:
        print("Seed buyer already exists: buyer@oldpages.in")
        return existing

    user = User(
        email="buyer@oldpages.in",
        email_verified_at=utc_now(),
        password_hash=hash_password(DEMO_PASSWORD),
        status="active",
    )
    repo.add(user)
    await repo.flush()
    repo.add(UserProfile(user_id=user.id, display_name="OldPages Buyer", username="buyer"))
    repo.add(UserPreference(user_id=user.id))
    await repo.commit()
    print("Created seed buyer: buyer@oldpages.in / OldPagesDemo!2026")
    return user


async def seed_moderator_identity(session: AsyncSession) -> User:
    repo = IdentityRepository(session)
    existing = await repo.get_user_by_email("moderator@oldpages.in")
    if existing is not None:
        preference = await repo.get_preferences_by_user_id(existing.id)
        if preference is None:
            preference = UserPreference(user_id=existing.id, metadata_json={"roles": ["moderator"]})
            repo.add(preference)
            await repo.commit()
        roles = preference.metadata_json.get("roles", [])
        if not isinstance(roles, list):
            roles = []
        if "moderator" not in roles:
            preference.metadata_json = {
                **preference.metadata_json,
                "roles": [*roles, "moderator"],
            }
            await repo.commit()
        print("Seed moderator already exists: moderator@oldpages.in")
        return existing

    user = User(
        email="moderator@oldpages.in",
        email_verified_at=utc_now(),
        password_hash=hash_password(DEMO_PASSWORD),
        status="active",
    )
    repo.add(user)
    await repo.flush()
    repo.add(UserProfile(user_id=user.id, display_name="OldPages Moderator", username="moderator"))
    repo.add(UserPreference(user_id=user.id, metadata_json={"roles": ["moderator"]}))
    await repo.commit()
    print("Created seed moderator: moderator@oldpages.in / OldPagesDemo!2026")
    return user


async def seed_catalog(session: AsyncSession, actor: User) -> None:
    repo = CatalogRepository(session)
    fiction = await ensure_category(repo, name="Fiction", slug="fiction")
    academic = await ensure_category(repo, name="Academic", slug="academic")
    textbooks = await ensure_category(
        repo,
        name="Textbooks",
        slug="textbooks",
        parent=academic,
    )
    await ensure_category(
        repo,
        name="Computer Science",
        slug="computer-science",
        parent=textbooks,
    )
    await repo.flush()

    existing = await repo.get_edition_by_identifier("isbn13", "9780143039433")
    if existing is not None:
        await repo.commit()
        print("Seed catalog book already exists: Godaan")
        return

    await CatalogService(session).create_book(
        BookCreateRequest(
            academic_metadata=AcademicMetadataInput(
                course="Hindi Literature",
                degree="BA",
                subject="Hindi",
            ),
            authors=[AuthorInput(name="Munshi Premchand")],
            category_ids=[fiction.public_id],
            description="A canonical Hindi novel used as sample catalog metadata.",
            edition="Paperback",
            format="paperback",
            genres=["Literary Fiction"],
            isbn_13="9780143039433",
            language="hi",
            page_count=320,
            publication_year=2019,
            publisher=PublisherInput(name="Penguin Classics"),
            subjects=["Indian literature"],
            title="Godaan",
        ),
        actor,
        AuthenticatedRequestContext(),
    )
    print("Created seed catalog book: Godaan / 9780143039433")


async def seed_listing(session: AsyncSession, actor: User) -> None:
    repo = ListingRepository(session)
    edition = await repo.get_book_edition_by_isbn("isbn13", "9780143039433")
    if edition is None:
        print("Seed listing skipped: catalog book is missing")
        return

    existing = await session.execute(
        select(Listing).where(
            Listing.book_edition_id == edition.id,
            Listing.seller_user_id == actor.id,
            Listing.status != "deleted",
        )
    )
    if existing.scalar_one_or_none() is not None:
        print("Seed listing already exists: Godaan")
        return

    media_public_id = new_ulid()
    storage_key = f"seed/{actor.public_id}/{media_public_id}/godaan.jpg"
    media = MediaAsset(
        byte_size=512_000,
        content_type="image/jpeg",
        original_filename="godaan.jpg",
        public_id=media_public_id,
        public_url=f"http://localhost:9000/oldpages-media/{storage_key}",
        status="approved",
        storage_key=storage_key,
        upload_expires_at=utc_now() + timedelta(minutes=15),
        user_id=actor.id,
    )
    session.add(media)
    await session.flush()

    service = ListingService(session, get_settings())
    listing = await service.create_listing(
        ListingCreateRequest(
            book_id=edition.public_id,
            condition=ListingConditionInput(
                condition="good",
                damage_details="Light shelf wear.",
                highlighting_percent=5,
            ),
            delivery_methods=[ListingDeliveryMethodInput(method="pickup")],
            description="A clean used copy of Godaan available for local pickup.",
            images=[ListingImageInput(media_id=media.public_id, alt_text="Godaan cover")],
            listing_modes=["sell"],
            location=ListingLocationInput(
                campus_pickup=True,
                city="Pune",
                country="IN",
                exact_latitude="18.520430",
                exact_longitude="73.856744",
                neighborhood="Deccan",
                public_area="Deccan, Pune",
                state="Maharashtra",
            ),
            price_amount_cents=25000,
        ),
        actor,
        AuthenticatedRequestContext(),
    )
    await service.publish_listing(listing.id, actor, AuthenticatedRequestContext())
    print("Created seed listing: Godaan / sell")


async def seed_chat(session: AsyncSession, seller: User) -> None:
    buyer = await seed_buyer_identity(session)
    listing_result = await session.execute(
        select(Listing)
        .where(
            Listing.seller_user_id == seller.id,
            Listing.status == "active",
        )
        .order_by(Listing.id)
    )
    listing = listing_result.scalars().first()
    if listing is None:
        print("Seed chat skipped: active listing is missing")
        return

    request_result = await session.execute(
        select(ChatRequest).where(
            ChatRequest.listing_id == listing.id,
            ChatRequest.requester_user_id == buyer.id,
            ChatRequest.recipient_user_id == seller.id,
            ChatRequest.status == "accepted",
        )
    )
    if request_result.scalar_one_or_none() is not None:
        print("Seed chat already exists: buyer@oldpages.in -> demo@oldpages.in")
        return

    service = ChatService(session)
    chat_request = await service.create_chat_request(
        ChatRequestCreateRequest(
            listing_id=listing.public_id,
            message="Is this copy still available?",
        ),
        buyer,
        AuthenticatedRequestContext(),
    )
    accepted = await service.accept_chat_request(
        chat_request.id,
        ChatRequestActionRequest(message="Yes, pickup near Deccan works."),
        seller,
        AuthenticatedRequestContext(),
    )
    if accepted.conversation_id is not None:
        await service.send_message(
            accepted.conversation_id,
            MessageCreateRequest(
                body="Great, I can collect it this evening.",
                client_message_id="seed-chat-message-1",
            ),
            buyer,
            AuthenticatedRequestContext(),
        )
    print("Created seed chat: buyer@oldpages.in -> demo@oldpages.in")


async def seed_offer(session: AsyncSession, seller: User) -> None:
    buyer = await seed_buyer_identity(session)
    listing_result = await session.execute(
        select(Listing)
        .where(
            Listing.seller_user_id == seller.id,
            Listing.status == "active",
        )
        .order_by(Listing.id)
    )
    listing = listing_result.scalars().first()
    if listing is None:
        print("Seed offer skipped: active listing is missing")
        return

    offer_result = await session.execute(
        select(CommerceOffer).where(
            CommerceOffer.listing_id == listing.id,
            CommerceOffer.buyer_user_id == buyer.id,
            CommerceOffer.status.in_(["pending", "accepted"]),
        )
    )
    if offer_result.scalar_one_or_none() is not None:
        print("Seed offer already exists: buyer@oldpages.in -> demo@oldpages.in")
        return

    await CommerceService(session).create_offer(
        OfferCreateRequest(
            amount_cents=22000,
            fulfillment_method="pickup",
            listing_id=listing.public_id,
            message="Would you take 220 for local pickup?",
        ),
        buyer,
        AuthenticatedRequestContext(),
    )
    print("Created seed offer: buyer@oldpages.in -> demo@oldpages.in")


async def seed_report(session: AsyncSession, seller: User) -> None:
    buyer = await seed_buyer_identity(session)
    listing_result = await session.execute(
        select(Listing)
        .where(
            Listing.seller_user_id == seller.id,
            Listing.status == "active",
        )
        .order_by(Listing.id)
    )
    listing = listing_result.scalars().first()
    if listing is None:
        print("Seed report skipped: active listing is missing")
        return

    report_result = await session.execute(
        select(Report).where(
            Report.reporter_user_id == buyer.id,
            Report.target_listing_id == listing.id,
            Report.reason == "fake_listing",
        )
    )
    if report_result.scalar_one_or_none() is not None:
        print("Seed report already exists: buyer@oldpages.in -> demo listing")
        return

    await TrustService(session).create_report(
        ReportCreateRequest(
            description="Demo report for the moderator queue.",
            evidence={"seed": True},
            reason="fake_listing",
            target_id=listing.public_id,
            target_type="listing",
        ),
        buyer,
        AuthenticatedRequestContext(),
    )
    print("Created seed report: buyer@oldpages.in -> demo listing")


async def seed_community(session: AsyncSession, owner: User) -> None:
    existing = await session.execute(select(Community).where(Community.slug == "pune-readers"))
    if existing.scalar_one_or_none() is not None:
        print("Seed community already exists: Pune Readers")
        return

    await CommunityService(session).create_community(
        CommunityCreateRequest(
            city="Pune",
            community_type="city",
            country="IN",
            description="Local reading, exchange, and used-book conversations for Pune.",
            name="Pune Readers",
            slug="pune-readers",
            state="Maharashtra",
            visibility="public",
        ),
        owner,
        AuthenticatedRequestContext(),
    )
    print("Created seed community: Pune Readers")


async def seed_clubs_events(session: AsyncSession, owner: User) -> None:
    repo = ListingRepository(session)
    edition = await repo.get_book_edition_by_isbn("isbn13", "9780143039433")
    if edition is None:
        print("Seed clubs/events skipped: catalog book is missing")
        return

    community_result = await session.execute(
        select(Community).where(Community.slug == "pune-readers")
    )
    community = community_result.scalar_one_or_none()
    service = ClubService(session)

    club_result = await session.execute(
        select(BookClub).where(BookClub.slug == "pune-readers-book-club")
    )
    club = club_result.scalar_one_or_none()
    if club is None:
        await service.create_club(
            BookClubCreateRequest(
                community_id=community.public_id if community else None,
                description="A public monthly club anchored to the Pune Readers community.",
                name="Pune Readers Book Club",
                slug="pune-readers-book-club",
                timezone="Asia/Kolkata",
                visibility="public",
            ),
            owner,
            AuthenticatedRequestContext(),
        )
        club_result = await session.execute(
            select(BookClub).where(BookClub.slug == "pune-readers-book-club")
        )
        club = club_result.scalar_one()
        print("Created seed book club: Pune Readers Book Club")
    else:
        print("Seed book club already exists: Pune Readers Book Club")

    club_book_result = await session.execute(
        select(ClubBook).where(
            ClubBook.book_edition_id == edition.id,
            ClubBook.club_id == club.id,
            ClubBook.status == "current",
        )
    )
    club_book = club_book_result.scalar_one_or_none()
    if club_book is None:
        club_book_response = await service.add_club_book(
            club.public_id,
            ClubBookCreateRequest(
                book_id=edition.public_id,
                discussion_guide="Discuss agrarian debt, family obligations, and social change.",
                end_date=date(2026, 7, 31),
                start_date=date(2026, 7, 1),
                status="current",
            ),
            owner,
            AuthenticatedRequestContext(),
        )
        club_book_result = await session.execute(
            select(ClubBook).where(ClubBook.public_id == club_book_response.id)
        )
        club_book = club_book_result.scalar_one()
        print("Created seed club book: Godaan")
    else:
        print("Seed club book already exists: Godaan")

    milestone_result = await session.execute(
        select(ReadingMilestone).where(
            ReadingMilestone.club_book_id == club_book.id,
            ReadingMilestone.title == "Week 1: Opening Chapters",
        )
    )
    if milestone_result.scalar_one_or_none() is None:
        await service.create_milestone(
            club_book.public_id,
            ReadingMilestoneCreateRequest(
                discussion_prompt="What social pressures shape Hori's earliest choices?",
                position_type="page",
                position_value=75,
                title="Week 1: Opening Chapters",
            ),
            owner,
            AuthenticatedRequestContext(),
        )
        print("Created seed reading milestone: Week 1")
    else:
        print("Seed reading milestone already exists: Week 1")

    event_result = await session.execute(
        select(Event).where(
            Event.club_id == club.id,
            Event.title == "Pune Readers Book Exchange Evening",
        )
    )
    if event_result.scalar_one_or_none() is None:
        starts_at = datetime(2026, 7, 12, 18, 30, tzinfo=ZoneInfo("Asia/Kolkata"))
        await service.create_event(
            EventCreateRequest(
                address="Deccan, Pune",
                capacity=25,
                club_id=club.public_id,
                description="Bring one used book to exchange and discuss the club's current pick.",
                ends_at=starts_at + timedelta(hours=2),
                event_type="book_exchange",
                location_name="Community library",
                starts_at=starts_at,
                timezone="Asia/Kolkata",
                title="Pune Readers Book Exchange Evening",
                visibility="public",
            ),
            owner,
            AuthenticatedRequestContext(),
        )
        print("Created seed event: Pune Readers Book Exchange Evening")
    else:
        print("Seed event already exists: Pune Readers Book Exchange Evening")


async def seed_reading_tracker(session: AsyncSession, owner: User) -> None:
    repo = CatalogRepository(session)
    edition = await repo.get_edition_by_identifier("isbn13", "9780143039433")
    if edition is None:
        print("Seed reading tracker skipped: catalog book is missing")
        return

    service = ReadingService(session)
    progress_result = await session.execute(
        select(ReadingProgress).where(
            ReadingProgress.book_edition_id == edition.id,
            ReadingProgress.user_id == owner.id,
        )
    )
    if progress_result.scalar_one_or_none() is None:
        await service.update_progress(
            edition.public_id,
            ReadingProgressUpdateRequest(
                current_page=160,
                progressed_on=date(2026, 7, 1),
                reading_minutes=45,
                started_on=date(2026, 7, 1),
                status="currently_reading",
            ),
            owner,
            AuthenticatedRequestContext(),
        )
        print("Created seed reading progress: Godaan")
    else:
        print("Seed reading progress already exists: Godaan")

    note_result = await session.execute(
        select(ReadingNote).where(
            ReadingNote.client_note_id == "seed-reading-note-1",
            ReadingNote.user_id == owner.id,
        )
    )
    if note_result.scalar_one_or_none() is None:
        await service.create_note(
            ReadingNoteCreateRequest(
                body="Track agrarian debt and family obligation themes for the July discussion.",
                book_id=edition.public_id,
                client_note_id="seed-reading-note-1",
                note_type="note",
                page_number=160,
                percent_complete=50,
                visibility="private",
            ),
            owner,
            AuthenticatedRequestContext(),
        )
        print("Created seed reading note: Godaan")
    else:
        print("Seed reading note already exists: Godaan")

    goal_result = await session.execute(
        select(ReadingGoal).where(
            ReadingGoal.goal_type == "books_per_year",
            ReadingGoal.period_start == date(2026, 1, 1),
            ReadingGoal.scope == "personal",
            ReadingGoal.user_id == owner.id,
        )
    )
    if goal_result.scalar_one_or_none() is None:
        await service.create_goal(
            ReadingGoalCreateRequest(
                goal_type="books_per_year",
                period_end=date(2026, 12, 31),
                period_start=date(2026, 1, 1),
                target_value=24,
                timezone="Asia/Kolkata",
            ),
            owner,
            AuthenticatedRequestContext(),
        )
        print("Created seed reading goal: 24 books in 2026")
    else:
        print("Seed reading goal already exists: 24 books in 2026")

    await service.recompute_statistics(
        ReadingStatisticRecomputeRequest(
            period_start=date(2026, 1, 1),
            period_type="year",
            timezone="Asia/Kolkata",
        ),
        owner,
        AuthenticatedRequestContext(),
    )
    print("Recomputed seed reading statistics: 2026")


async def ensure_category(
    repo: CatalogRepository,
    *,
    name: str,
    slug: str,
    parent: Category | None = None,
) -> Category:
    existing = await repo.get_category_by_public_id_or_slug(slug)
    if existing is not None:
        return existing
    category = Category(name=name, parent_id=parent.id if parent else None, slug=slug)
    repo.add(category)
    await repo.flush()
    return category


async def run() -> None:
    async with get_session_factory()() as session:
        user = await seed_identity(session)
        await seed_moderator_identity(session)
        await seed_catalog(session, user)
        await seed_listing(session, user)
        await seed_chat(session, user)
        await seed_offer(session, user)
        await seed_report(session, user)
        await seed_community(session, user)
        await seed_clubs_events(session, user)
        await seed_reading_tracker(session, user)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
