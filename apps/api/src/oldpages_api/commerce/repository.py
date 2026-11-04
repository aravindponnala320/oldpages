from __future__ import annotations

from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.commerce.models import (
    ExchangeOfferItem,
    Offer,
    PickupSession,
    Review,
    ReviewDimension,
    Transaction,
)
from oldpages_api.identity.models import User, UserProfile
from oldpages_api.listings.models import (
    Listing,
    ListingInventory,
)


class CommerceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_listing_by_public_id(self, public_id: str) -> Listing | None:
        result = await self.session.execute(
            select(Listing)
            .execution_options(populate_existing=True)
            .options(*listing_load_options())
            .where(Listing.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_listing_by_id(self, listing_id: int) -> Listing | None:
        result = await self.session.execute(
            select(Listing)
            .execution_options(populate_existing=True)
            .options(*listing_load_options())
            .where(Listing.id == listing_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_offer_by_public_id(self, public_id: str) -> Offer | None:
        result = await self.session.execute(
            select(Offer)
            .execution_options(populate_existing=True)
            .options(*offer_load_options())
            .where(Offer.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_transaction_by_public_id(self, public_id: str) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction)
            .execution_options(populate_existing=True)
            .options(*transaction_load_options())
            .where(Transaction.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_pickup_by_public_id(self, public_id: str) -> PickupSession | None:
        result = await self.session.execute(
            select(PickupSession)
            .execution_options(populate_existing=True)
            .options(*pickup_load_options())
            .where(PickupSession.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_pickup_for_transaction(self, transaction_id: int) -> PickupSession | None:
        result = await self.session.execute(
            select(PickupSession)
            .execution_options(populate_existing=True)
            .options(*pickup_load_options())
            .where(PickupSession.transaction_id == transaction_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_review_for_reviewer(
        self,
        transaction_id: int,
        reviewer_user_id: int,
    ) -> Review | None:
        result = await self.session.execute(
            select(Review).where(
                Review.transaction_id == transaction_id,
                Review.reviewer_user_id == reviewer_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_review_by_public_id(self, public_id: str) -> Review | None:
        result = await self.session.execute(
            select(Review)
            .execution_options(populate_existing=True)
            .options(*review_load_options())
            .where(Review.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_offers_for_user(
        self,
        user_id: int,
        role: str = "buyer",
        listing_id: int | None = None,
        limit: int = 50,
    ) -> list[Offer]:
        if role == "seller":
            condition = Offer.seller_user_id == user_id
        else:
            condition = Offer.buyer_user_id == user_id
        stmt = (
            select(Offer)
            .options(*offer_load_options())
            .where(condition, Offer.status != "withdrawn")
            .order_by(Offer.created_at.desc())
            .limit(limit)
        )
        if listing_id is not None:
            stmt = stmt.where(Offer.listing_id == listing_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_transactions_for_user(
        self,
        user_id: int,
        role: str = "buyer",
        limit: int = 50,
    ) -> list[Transaction]:
        if role == "seller":
            condition = Transaction.seller_user_id == user_id
        else:
            condition = Transaction.buyer_user_id == user_id
        stmt = (
            select(Transaction)
            .options(*transaction_load_options())
            .where(condition)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def reserve_inventory(self, listing_id: int, quantity: int) -> bool:
        result = await self.session.execute(
            update(ListingInventory)
            .where(
                ListingInventory.listing_id == listing_id,
                ListingInventory.quantity_available >= quantity,
            )
            .values(quantity_available=ListingInventory.quantity_available - quantity)
        )
        return cast("CursorResult[Any]", result).rowcount == 1

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def listing_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Listing.delivery_methods),
        selectinload(Listing.inventory),
        selectinload(Listing.location),
        selectinload(Listing.seller),
    )


def offer_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Offer.buyer).selectinload(User.profile),
        selectinload(Offer.exchange_items).selectinload(ExchangeOfferItem.offered_listing),
        selectinload(Offer.listing).selectinload(Listing.delivery_methods),
        selectinload(Offer.listing).selectinload(Listing.inventory),
        selectinload(Offer.listing).selectinload(Listing.location),
        selectinload(Offer.listing).selectinload(Listing.seller),
        selectinload(Offer.parent),
        selectinload(Offer.proposer).selectinload(User.profile),
        selectinload(Offer.seller).selectinload(User.profile),
        selectinload(Offer.transaction),
    )


def transaction_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Transaction.buyer).selectinload(User.profile),
        selectinload(Transaction.listing).selectinload(Listing.delivery_methods),
        selectinload(Transaction.listing).selectinload(Listing.inventory),
        selectinload(Transaction.listing).selectinload(Listing.location),
        selectinload(Transaction.listing).selectinload(Listing.seller),
        selectinload(Transaction.offer),
        selectinload(Transaction.pickup_sessions).selectinload(PickupSession.confirmed_by),
        selectinload(Transaction.pickup_sessions).selectinload(PickupSession.proposed_by),
        selectinload(Transaction.reviews).selectinload(Review.dimensions),
        selectinload(Transaction.seller).selectinload(User.profile),
    )


def pickup_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(PickupSession.confirmed_by),
        selectinload(PickupSession.proposed_by),
        selectinload(PickupSession.transaction).selectinload(Transaction.buyer),
        selectinload(PickupSession.transaction).selectinload(Transaction.offer),
        selectinload(PickupSession.transaction).selectinload(Transaction.seller),
        selectinload(PickupSession.transaction)
        .selectinload(Transaction.listing)
        .selectinload(Listing.delivery_methods),
        selectinload(PickupSession.transaction)
        .selectinload(Transaction.listing)
        .selectinload(Listing.inventory),
        selectinload(PickupSession.transaction)
        .selectinload(Transaction.listing)
        .selectinload(Listing.location),
        selectinload(PickupSession.transaction)
        .selectinload(Transaction.listing)
        .selectinload(Listing.seller),
    )


def review_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Review.dimensions),
        selectinload(Review.reviewee),
        selectinload(Review.reviewer),
        selectinload(Review.transaction),
    )


__all__ = [
    "CommerceRepository",
    "ExchangeOfferItem",
    "Offer",
    "PickupSession",
    "Review",
    "ReviewDimension",
    "Transaction",
]
