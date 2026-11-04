from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.catalog.models import BookEdition
from oldpages_api.listings.models import (
    Listing,
    ListingCondition,
    ListingDeliveryMethod,
    ListingImage,
    ListingInventory,
    ListingLocation,
    ListingPriceHistory,
    MediaAsset,
)


class ListingRepository:
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

    async def get_media_by_public_id(self, public_id: str) -> MediaAsset | None:
        result = await self.session.execute(
            select(MediaAsset).where(MediaAsset.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_linked_image_for_media(self, media_asset_id: int) -> ListingImage | None:
        result = await self.session.execute(
            select(ListingImage).where(ListingImage.media_asset_id == media_asset_id)
        )
        return result.scalar_one_or_none()

    async def get_book_edition_by_public_id(self, public_id: str) -> BookEdition | None:
        result = await self.session.execute(
            select(BookEdition)
            .options(selectinload(BookEdition.identifiers))
            .where(BookEdition.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_book_edition_by_isbn(
        self, identifier_type: str, value: str
    ) -> BookEdition | None:
        from oldpages_api.catalog.models import BookIdentifier

        result = await self.session.execute(
            select(BookEdition)
            .join(BookIdentifier)
            .options(selectinload(BookEdition.identifiers))
            .where(
                BookIdentifier.identifier_type == identifier_type,
                BookIdentifier.identifier_value == value,
            )
        )
        return result.scalar_one_or_none()

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


def listing_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Listing.book_edition).selectinload(BookEdition.identifiers),
        selectinload(Listing.condition),
        selectinload(Listing.delivery_methods),
        selectinload(Listing.images).selectinload(ListingImage.media_asset),
        selectinload(Listing.inventory),
        selectinload(Listing.location),
        selectinload(Listing.price_history),
        selectinload(Listing.seller),
    )


__all__ = [
    "Listing",
    "ListingCondition",
    "ListingDeliveryMethod",
    "ListingImage",
    "ListingInventory",
    "ListingLocation",
    "ListingPriceHistory",
    "ListingRepository",
    "MediaAsset",
]
