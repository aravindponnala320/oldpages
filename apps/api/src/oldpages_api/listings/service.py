from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.catalog.exceptions import CatalogEntryNotFoundError
from oldpages_api.catalog.isbn import normalize_isbn
from oldpages_api.catalog.models import BookEdition
from oldpages_api.core.config import Settings
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.listings.events import (
    LISTING_CREATED,
    LISTING_DELETED,
    LISTING_PAUSED,
    LISTING_PUBLISHED,
    LISTING_RELISTED,
    LISTING_UPDATED,
    MEDIA_UPLOAD_COMPLETED,
    MEDIA_UPLOAD_REQUESTED,
)
from oldpages_api.listings.exceptions import (
    InvalidListingStateTransitionError,
    ListingNotFoundError,
    ListingValidationError,
    MediaAssetNotFoundError,
    MediaValidationError,
)
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
from oldpages_api.listings.permissions import require_listing_owner, require_media_owner
from oldpages_api.listings.repository import ListingRepository
from oldpages_api.listings.schemas import (
    PRICE_REQUIRED_MODES,
    CompleteMediaUploadRequest,
    ConditionGrade,
    DeliveryMethod,
    ListingBookSummary,
    ListingConditionInput,
    ListingConditionResponse,
    ListingCreateRequest,
    ListingDeliveryMethodInput,
    ListingDeliveryMethodResponse,
    ListingImageInput,
    ListingImageResponse,
    ListingInventoryResponse,
    ListingLocationInput,
    ListingLocationPublicResponse,
    ListingMode,
    ListingPriceHistoryResponse,
    ListingResponse,
    ListingSellerSummary,
    ListingStatus,
    ListingUpdateRequest,
    MediaAssetResponse,
    MediaStatus,
    MediaUploadUrlRequest,
    MediaUploadUrlResponse,
    validate_price_rules,
)
from oldpages_api.listings.tasks import enqueue_media_processing, refresh_listing_search_document
from oldpages_api.shared.db.ids import new_ulid

_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9_.-]+")


class ListingService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.repo = ListingRepository(session)
        self.session = session
        self.settings = settings

    async def create_upload_url(
        self,
        payload: MediaUploadUrlRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> MediaUploadUrlResponse:
        media_public_id = new_ulid()
        storage_key = (
            f"media/{actor.public_id}/{media_public_id}/{sanitize_filename(payload.filename)}"
        )
        expires_at = utc_now() + timedelta(minutes=15)
        media = MediaAsset(
            byte_size=payload.byte_size,
            checksum_sha256=payload.checksum_sha256,
            content_type=payload.content_type,
            original_filename=payload.filename,
            public_id=media_public_id,
            status="pending_upload",
            storage_key=storage_key,
            upload_expires_at=expires_at,
            user_id=actor.id,
        )
        self.repo.add(media)
        await self.audit(
            action=MEDIA_UPLOAD_REQUESTED,
            actor=actor,
            context=context,
            payload={"media_id": media_public_id, "storage_key": storage_key},
        )
        await self.repo.commit()
        return MediaUploadUrlResponse(
            expires_at=expires_at,
            headers={"Content-Type": payload.content_type},
            id=media_public_id,
            storage_key=storage_key,
            upload_url=self.development_upload_url(storage_key),
        )

    async def complete_upload(
        self,
        media_id: str,
        payload: CompleteMediaUploadRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> MediaAssetResponse:
        media = await self.repo.get_media_by_public_id(media_id)
        if media is None:
            raise MediaAssetNotFoundError()
        require_media_owner(actor, media)
        if media.status != "pending_upload":
            raise MediaValidationError("Only pending uploads can be completed.")
        if as_utc(media.upload_expires_at) < utc_now():
            raise MediaValidationError("The upload URL has expired.")
        if payload.byte_size is not None and payload.byte_size != media.byte_size:
            raise MediaValidationError("Uploaded byte size does not match the requested upload.")
        if payload.checksum_sha256 is not None:
            media.checksum_sha256 = payload.checksum_sha256
        media.status = "uploaded"
        await enqueue_media_processing(media.id)
        await self.audit(
            action=MEDIA_UPLOAD_COMPLETED,
            actor=actor,
            context=context,
            payload={"media_id": media.public_id},
        )
        await self.repo.commit()
        return media_response(media)

    async def create_listing(
        self,
        payload: ListingCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ListingResponse:
        book_edition = await self.resolve_book_edition(
            payload.book_id, payload.isbn, payload.book_title, payload.book_author
        )
        validate_price_rules(payload.listing_modes, payload.price_amount_cents)

        # Resolve business/institution internal IDs from public IDs
        business_db_id: int | None = None
        institution_db_id: int | None = None
        if payload.scope == "business" and payload.business_profile_id:
            from sqlalchemy import select as sa_select
            from oldpages_api.business.models import BusinessProfile
            bp_result = await self.session.execute(
                sa_select(BusinessProfile).where(
                    BusinessProfile.public_id == payload.business_profile_id,
                    BusinessProfile.owner_user_id == actor.id,
                    BusinessProfile.status == "active",
                )
            )
            bp = bp_result.scalar_one_or_none()
            if bp is None:
                from oldpages_api.listings.exceptions import ListingValidationError
                raise ListingValidationError("Active business profile not found or you are not the owner.")
            business_db_id = bp.id
        if payload.scope == "institution" and payload.institution_id:
            from sqlalchemy import select as sa_select
            from oldpages_api.institutions.models import Institution
            inst_result = await self.session.execute(
                sa_select(Institution).where(
                    Institution.public_id == payload.institution_id,
                    Institution.owner_user_id == actor.id,
                    Institution.status == "active",
                )
            )
            inst = inst_result.scalar_one_or_none()
            if inst is None:
                from oldpages_api.listings.exceptions import ListingValidationError
                raise ListingValidationError("Active institution not found or you are not the owner.")
            institution_db_id = inst.id

        listing = Listing(
            book_edition_id=book_edition.id,
            business_profile_id=business_db_id,
            institution_id=institution_db_id,
            currency=payload.currency,
            description=payload.description,
            exchange_preferences=payload.exchange_preferences,
            open_to_exchange=payload.open_to_exchange,
            lending_duration_days=payload.lending_duration_days,
            listing_modes=list(payload.listing_modes),
            negotiable=payload.negotiable,
            price_amount_cents=payload.price_amount_cents,
            rental_fee_per_day_cents=payload.rental_fee_per_day_cents,
            rental_deposit_amount_cents=payload.rental_deposit_amount_cents,
            return_policy=payload.return_policy,
            scope=payload.scope,
            visibility=payload.visibility,
            seller_user_id=actor.id,
            status="draft",
            title_snapshot=book_edition.title,
        )
        self.repo.add(listing)
        await self.repo.flush()
        self.repo.add(condition_from_input(payload.condition, listing.id))
        self.repo.add(location_from_input(payload.location, listing.id))
        self.repo.add(
            ListingInventory(
                listing_id=listing.id,
                quantity_available=payload.quantity,
                quantity_total=payload.quantity,
            )
        )
        add_delivery_methods(self.repo, listing.id, payload.delivery_methods)
        await self.replace_images(listing, payload.images, actor, replace_existing=False)
        if payload.price_amount_cents is not None:
            self.repo.add(
                ListingPriceHistory(
                    changed_by_user_id=actor.id,
                    currency=payload.currency,
                    listing_id=listing.id,
                    new_amount_cents=payload.price_amount_cents,
                    old_amount_cents=None,
                    reason="initial_price",
                )
            )
        listing.quality_score = calculate_create_quality_score(payload, book_edition)
        await self.audit(
            action=LISTING_CREATED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id},
        )
        await self.repo.commit()
        reloaded = await self.get_listing_model(listing.public_id)
        return listing_response(reloaded)

    async def get_my_listings(
        self,
        actor: User,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ListingResponse]:
        from sqlalchemy import select as sa_select
        from oldpages_api.listings.repository import ListingRepository
        repo = ListingRepository(self.session)
        stmt = (
            sa_select(Listing)
            .where(
                Listing.seller_user_id == actor.id,
                Listing.status != "deleted",
            )
            .order_by(Listing.id.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Listing.status == status)
        result = await self.session.execute(stmt)
        listings = list(result.unique().scalars().all())
        # Eagerly load relationships
        loaded = []
        for listing in listings:
            full = await repo.get_listing_by_public_id(listing.public_id)
            if full:
                loaded.append(listing_response(full))
        return loaded

    async def get_listing(self, listing_id: str) -> ListingResponse:
        listing = await self.get_listing_model(listing_id)
        if listing.status == "deleted":
            raise ListingNotFoundError()
        return listing_response(listing)

    async def update_listing(
        self,
        listing_id: str,
        payload: ListingUpdateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ListingResponse:
        listing = await self.get_listing_model(listing_id)
        require_listing_owner(actor, listing)
        ensure_editable(listing)
        fields = payload.model_fields_set

        next_modes = (
            payload.listing_modes if payload.listing_modes is not None else listing.listing_modes
        )
        next_price = (
            payload.price_amount_cents
            if "price_amount_cents" in fields
            else listing.price_amount_cents
        )
        validate_price_rules(cast("list[ListingMode]", next_modes), next_price)

        old_price = listing.price_amount_cents
        if payload.listing_modes is not None:
            listing.listing_modes = list(payload.listing_modes)
        if "description" in fields:
            listing.description = payload.description
        if "price_amount_cents" in fields:
            listing.price_amount_cents = payload.price_amount_cents
        if payload.currency is not None:
            listing.currency = payload.currency
        if payload.negotiable is not None:
            listing.negotiable = payload.negotiable
        if "return_policy" in fields:
            listing.return_policy = payload.return_policy
        if "exchange_preferences" in fields:
            listing.exchange_preferences = payload.exchange_preferences
        if "open_to_exchange" in fields:
            listing.open_to_exchange = payload.open_to_exchange or False
        if "lending_duration_days" in fields:
            listing.lending_duration_days = payload.lending_duration_days
        if "rental_fee_per_day_cents" in fields:
            listing.rental_fee_per_day_cents = payload.rental_fee_per_day_cents
        if "rental_deposit_amount_cents" in fields:
            listing.rental_deposit_amount_cents = payload.rental_deposit_amount_cents
        if payload.quantity is not None:
            if listing.inventory is None:
                listing.inventory = ListingInventory(
                    listing_id=listing.id,
                    quantity_available=payload.quantity,
                    quantity_total=payload.quantity,
                )
            else:
                listing.inventory.quantity_total = payload.quantity
                listing.inventory.quantity_available = min(
                    listing.inventory.quantity_available,
                    payload.quantity,
                )
        if payload.condition is not None:
            if listing.condition is not None:
                await self.repo.delete(listing.condition)
                await self.repo.flush()
            self.repo.add(condition_from_input(payload.condition, listing.id))
        if payload.location is not None:
            if listing.location is not None:
                await self.repo.delete(listing.location)
                await self.repo.flush()
            self.repo.add(location_from_input(payload.location, listing.id))
        if payload.delivery_methods is not None:
            listing.delivery_methods.clear()
            await self.repo.flush()
            add_delivery_methods(self.repo, listing.id, payload.delivery_methods)
        if payload.images is not None:
            await self.replace_images(listing, payload.images, actor, replace_existing=True)

        if old_price != listing.price_amount_cents:
            self.repo.add(
                ListingPriceHistory(
                    changed_by_user_id=actor.id,
                    currency=listing.currency,
                    listing_id=listing.id,
                    new_amount_cents=listing.price_amount_cents,
                    old_amount_cents=old_price,
                    reason="manual_update",
                )
            )
        listing.quality_score = calculate_quality_score(listing)
        await self.audit(
            action=LISTING_UPDATED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id},
        )
        await self.repo.commit()
        await refresh_listing_search_document(listing.id)
        reloaded = await self.get_listing_model(listing.public_id)
        return listing_response(reloaded)

    async def publish_listing(
        self,
        listing_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ListingResponse:
        listing = await self.get_listing_model(listing_id)
        require_listing_owner(actor, listing)
        if listing.status not in {"draft", "paused", "expired"}:
            raise InvalidListingStateTransitionError(
                f"Cannot publish a listing from status '{listing.status}'."
            )
        validate_publish_ready(listing)
        listing.status = "active"
        listing.published_at = utc_now()
        listing.paused_at = None
        listing.expired_at = None
        listing.quality_score = calculate_quality_score(listing)
        await self.audit(
            action=LISTING_PUBLISHED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id},
        )
        await self.repo.commit()
        await refresh_listing_search_document(listing.id)
        reloaded = await self.get_listing_model(listing.public_id)
        return listing_response(reloaded)

    async def pause_listing(
        self,
        listing_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ListingResponse:
        listing = await self.get_listing_model(listing_id)
        require_listing_owner(actor, listing)
        if listing.status != "active":
            raise InvalidListingStateTransitionError("Only active listings can be paused.")
        listing.status = "paused"
        listing.paused_at = utc_now()
        await self.audit(
            action=LISTING_PAUSED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id},
        )
        await self.repo.commit()
        reloaded = await self.get_listing_model(listing.public_id)
        return listing_response(reloaded)

    async def relist_listing(
        self,
        listing_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ListingResponse:
        listing = await self.get_listing_model(listing_id)
        require_listing_owner(actor, listing)
        if listing.status not in {"paused", "expired"}:
            raise InvalidListingStateTransitionError(
                "Only paused or expired listings can be relisted."
            )
        validate_publish_ready(listing)
        listing.status = "active"
        listing.published_at = utc_now()
        listing.paused_at = None
        listing.expired_at = None
        listing.quality_score = calculate_quality_score(listing)
        await self.audit(
            action=LISTING_RELISTED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id},
        )
        await self.repo.commit()
        await refresh_listing_search_document(listing.id)
        reloaded = await self.get_listing_model(listing.public_id)
        return listing_response(reloaded)

    async def delete_listing(
        self,
        listing_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> None:
        listing = await self.get_listing_model(listing_id)
        require_listing_owner(actor, listing)
        if listing.status in {"deleted", "reserved", "completed"}:
            raise InvalidListingStateTransitionError(
                f"Cannot delete a listing from status '{listing.status}'."
            )
        listing.status = "deleted"
        listing.deleted_at = utc_now()
        await self.audit(
            action=LISTING_DELETED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id},
        )
        await self.repo.commit()

    async def resolve_book_edition(
        self,
        book_id: str | None,
        isbn: str | None,
        book_title: str | None = None,
        book_author: str | None = None,
    ) -> BookEdition:
        if book_id:
            edition = await self.repo.get_book_edition_by_public_id(book_id)
            if edition is None:
                raise CatalogEntryNotFoundError()
            return edition
        if isbn:
            normalized = normalize_isbn(isbn)
            edition = await self.repo.get_book_edition_by_isbn(
                normalized.identifier_type,
                normalized.value,
            )
            if edition is not None:
                return edition
            # ISBN not in catalog — auto-create a minimal entry
            if not book_title:
                raise ListingValidationError(
                    "Book not found in catalog. Please provide the book title along with the ISBN."
                )
            return await self._create_minimal_book_edition(
                title=book_title,
                author=book_author,
                isbn=isbn,
            )
        if book_title:
            return await self._create_minimal_book_edition(
                title=book_title,
                author=book_author,
            )
        raise ListingValidationError("Either book_id, isbn, or book_title is required.")

    async def _create_minimal_book_edition(
        self,
        title: str,
        author: str | None = None,
        isbn: str | None = None,
    ) -> BookEdition:
        from sqlalchemy import select as sa_select
        from oldpages_api.catalog.models import Author, Book, BookAuthor, BookIdentifier

        import hashlib

        def _normalize(v: str) -> str:
            return " ".join(v.strip().casefold().split())

        def _fingerprint(t: str, a: str | None, fmt: str, lang: str) -> str:
            raw = "|".join([_normalize(t), _normalize(a or ""), "", "", "", lang, fmt])
            return hashlib.sha256(raw.encode("utf-8")).hexdigest()

        # Create a Book record first, then a BookEdition linked to it
        book = Book(title=title, normalized_title=_normalize(title))
        self.session.add(book)
        await self.session.flush()

        edition = BookEdition(
            book_id=book.id,
            title=title,
            format="paperback",
            language="en",
            edition_fingerprint=_fingerprint(title, author, "paperback", "en"),
        )
        edition.identifiers = []
        edition.authors = []
        self.session.add(edition)
        await self.session.flush()

        if isbn:
            try:
                normalized = normalize_isbn(isbn)
                self.session.add(
                    BookIdentifier(
                        book_edition_id=edition.id,
                        identifier_type=normalized.identifier_type,
                        value=normalized.value,
                    )
                )
            except Exception:
                pass

        if author:
            result = await self.session.execute(
                sa_select(Author).where(Author.name == author.strip())
            )
            author_obj = result.scalar_one_or_none()
            if author_obj is None:
                author_obj = Author(name=author.strip())
                self.session.add(author_obj)
                await self.session.flush()
            self.session.add(BookAuthor(book_id=book.id, author_id=author_obj.id, position=1))

        await self.session.flush()
        return edition

    async def replace_images(
        self,
        listing: Listing,
        images: list[ListingImageInput],
        actor: User,
        *,
        replace_existing: bool,
    ) -> None:
        if replace_existing:
            listing.images.clear()
            await self.repo.flush()
        for index, image_input in enumerate(images):
            media = await self.repo.get_media_by_public_id(image_input.media_id)
            if media is None:
                raise MediaAssetNotFoundError()
            require_media_owner(actor, media)
            if media.status not in {"uploaded", "approved"}:
                raise MediaValidationError("Only uploaded or approved media can be attached.")
            linked_image = await self.repo.get_linked_image_for_media(media.id)
            if linked_image is not None and linked_image.listing_id != listing.id:
                raise MediaValidationError("Media asset is already attached to another listing.")
            self.repo.add(
                ListingImage(
                    alt_text=image_input.alt_text,
                    is_primary=image_input.is_primary or index == 0,
                    listing_id=listing.id,
                    media_asset_id=media.id,
                    sort_order=index,
                )
            )

    async def get_listing_model(self, listing_id: str) -> Listing:
        listing = await self.repo.get_listing_by_public_id(listing_id)
        if listing is None:
            raise ListingNotFoundError()
        return listing

    async def audit(
        self,
        *,
        action: str,
        actor: User,
        context: AuthenticatedRequestContext,
        payload: dict[str, str],
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

    def development_upload_url(self, storage_key: str) -> str:
        endpoint = self.settings.object_storage_endpoint.rstrip("/")
        bucket = self.settings.object_storage_bucket
        return f"{endpoint}/{bucket}/{storage_key}?upload=development"


def ensure_editable(listing: Listing) -> None:
    if listing.status in {"deleted", "reserved", "completed", "suspended"}:
        raise InvalidListingStateTransitionError(
            f"Cannot edit a listing from status '{listing.status}'."
        )


def validate_publish_ready(listing: Listing) -> None:
    if listing.condition is None:
        raise ListingValidationError("Condition details are required before publishing.")
    if listing.location is None:
        raise ListingValidationError("Approximate listing location is required before publishing.")
    if listing.inventory is None or listing.inventory.quantity_available < 1:
        raise ListingValidationError("Available inventory is required before publishing.")
    # Photos are recommended but not required for publishing
    if set(listing.listing_modes) & PRICE_REQUIRED_MODES and listing.price_amount_cents is None:
        raise ListingValidationError("Price is required before publishing this listing type.")


def add_delivery_methods(
    repo: ListingRepository,
    listing_id: int,
    delivery_methods: list[ListingDeliveryMethodInput],
) -> None:
    seen: set[str] = set()
    for item in delivery_methods:
        if item.method in seen:
            continue
        seen.add(item.method)
        repo.add(
            ListingDeliveryMethod(
                enabled=item.enabled,
                listing_id=listing_id,
                method=item.method,
                notes=item.notes,
                price_amount_cents=item.price_amount_cents,
            )
        )


def condition_from_input(payload: ListingConditionInput, listing_id: int) -> ListingCondition:
    return ListingCondition(listing_id=listing_id, **payload.model_dump())


def location_from_input(payload: ListingLocationInput, listing_id: int) -> ListingLocation:
    values = payload.model_dump()
    public_latitude, public_longitude = approximate_public_coordinates(
        payload.exact_latitude,
        payload.exact_longitude,
    )
    values["public_latitude"] = public_latitude
    values["public_longitude"] = public_longitude
    return ListingLocation(listing_id=listing_id, **values)


def approximate_public_coordinates(
    exact_latitude: str | None,
    exact_longitude: str | None,
) -> tuple[float | None, float | None]:
    if exact_latitude is None or exact_longitude is None:
        return None, None
    try:
        latitude = float(exact_latitude)
        longitude = float(exact_longitude)
    except ValueError:
        return None, None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None, None
    return round(latitude, 2), round(longitude, 2)


def calculate_quality_score(listing: Listing) -> int:
    score = 0
    score += min(len(listing.images), 4) * 5
    if listing.condition is not None:
        score += 10
        condition_values = [
            listing.condition.damage_details,
            listing.condition.highlighting_percent,
            listing.condition.dust_jacket_present,
            listing.condition.supplemental_media_present,
            listing.condition.access_code_status,
            listing.condition.answer_key_present,
            listing.condition.workbook_completion_percent,
            listing.condition.collectible_notes,
        ]
        condition_flags = [
            listing.condition.handwritten_notes,
            listing.condition.name_written_inside,
            listing.condition.torn_pages,
            listing.condition.missing_pages,
            listing.condition.loose_binding,
            listing.condition.water_damage,
            listing.condition.stains,
            listing.condition.odor_or_smoke_exposure,
            listing.condition.library_markings,
            listing.condition.stickers,
            listing.condition.signed_by_author,
            listing.condition.first_edition,
        ]
        if any(value is not None for value in condition_values) or any(condition_flags):
            score += 10
    if listing.book_edition and listing.book_edition.identifiers:
        score += 15
    if listing.description:
        score += 15 if len(listing.description.strip()) >= 40 else 8
    if (
        not (set(listing.listing_modes) & PRICE_REQUIRED_MODES)
        or listing.price_amount_cents is not None
    ):
        score += 15
    if listing.location is not None and listing.location.public_area and listing.location.city:
        score += 15
    return min(score, 100)


def calculate_create_quality_score(payload: ListingCreateRequest, book_edition: BookEdition) -> int:
    score = 0
    score += min(len(payload.images), 4) * 5
    score += 10
    if condition_has_detail(payload.condition):
        score += 10
    if book_edition.identifiers:
        score += 15
    if payload.description:
        score += 15 if len(payload.description.strip()) >= 40 else 8
    if (
        not (set(payload.listing_modes) & PRICE_REQUIRED_MODES)
        or payload.price_amount_cents is not None
    ):
        score += 15
    if payload.location.public_area and payload.location.city:
        score += 15
    return min(score, 100)


def condition_has_detail(condition: ListingConditionInput) -> bool:
    values = [
        condition.damage_details,
        condition.highlighting_percent,
        condition.dust_jacket_present,
        condition.supplemental_media_present,
        condition.access_code_status,
        condition.answer_key_present,
        condition.workbook_completion_percent,
        condition.collectible_notes,
    ]
    flags = [
        condition.handwritten_notes,
        condition.name_written_inside,
        condition.torn_pages,
        condition.missing_pages,
        condition.loose_binding,
        condition.water_damage,
        condition.stains,
        condition.odor_or_smoke_exposure,
        condition.library_markings,
        condition.stickers,
        condition.signed_by_author,
        condition.first_edition,
    ]
    return any(value is not None for value in values) or any(flags)


def listing_response(listing: Listing) -> ListingResponse:
    return ListingResponse(
        book=ListingBookSummary(
            id=listing.book_edition.public_id, title=listing.book_edition.title
        ),
        condition=condition_response(listing.condition),
        created_at=listing.created_at,
        currency=listing.currency,
        delivery_methods=[
            ListingDeliveryMethodResponse(
                enabled=method.enabled,
                method=cast("DeliveryMethod", method.method),
                notes=method.notes,
                price_amount_cents=method.price_amount_cents,
            )
            for method in sorted(listing.delivery_methods, key=lambda item: item.method)
        ],
        description=listing.description,
        exchange_preferences=listing.exchange_preferences,
        open_to_exchange=listing.open_to_exchange,
        scope=listing.scope,  # type: ignore[arg-type]
        visibility=listing.visibility,  # type: ignore[arg-type]
        business_profile_id=None,
        institution_id=None,
        id=listing.public_id,
        images=[
            image_response(image)
            for image in sorted(listing.images, key=lambda item: item.sort_order)
        ],
        inventory=inventory_response(listing.inventory),
        lending_duration_days=listing.lending_duration_days,
        rental_fee_per_day_cents=listing.rental_fee_per_day_cents,
        listing_modes=cast("list[ListingMode]", listing.listing_modes),
        location=location_public_response(listing.location),
        negotiable=listing.negotiable,
        price_amount_cents=listing.price_amount_cents,
        price_history=[
            ListingPriceHistoryResponse(
                changed_at=item.created_at,
                currency=item.currency,
                id=item.public_id,
                new_amount_cents=item.new_amount_cents,
                old_amount_cents=item.old_amount_cents,
                reason=item.reason,
            )
            for item in sorted(listing.price_history, key=lambda history: history.created_at)
        ],
        quality_score=listing.quality_score,
        rental_deposit_amount_cents=listing.rental_deposit_amount_cents,
        return_policy=listing.return_policy,
        seller=ListingSellerSummary(id=listing.seller.public_id),
        status=cast("ListingStatus", listing.status),
        title=listing.title_snapshot,
        updated_at=listing.updated_at,
    )


def condition_response(condition: ListingCondition | None) -> ListingConditionResponse | None:
    if condition is None:
        return None
    return ListingConditionResponse(
        access_code_status=condition.access_code_status,
        answer_key_present=condition.answer_key_present,
        collectible_notes=condition.collectible_notes,
        condition=cast("ConditionGrade", condition.condition),
        damage_details=condition.damage_details,
        dust_jacket_present=condition.dust_jacket_present,
        first_edition=condition.first_edition,
        handwritten_notes=condition.handwritten_notes,
        highlighting_percent=condition.highlighting_percent,
        library_markings=condition.library_markings,
        loose_binding=condition.loose_binding,
        missing_pages=condition.missing_pages,
        name_written_inside=condition.name_written_inside,
        odor_or_smoke_exposure=condition.odor_or_smoke_exposure,
        signed_by_author=condition.signed_by_author,
        stains=condition.stains,
        stickers=condition.stickers,
        supplemental_media_present=condition.supplemental_media_present,
        torn_pages=condition.torn_pages,
        water_damage=condition.water_damage,
        workbook_completion_percent=condition.workbook_completion_percent,
    )


def location_public_response(
    location: ListingLocation | None,
) -> ListingLocationPublicResponse | None:
    if location is None:
        return None
    return ListingLocationPublicResponse(
        campus_pickup=location.campus_pickup,
        city=location.city,
        country=location.country,
        neighborhood=location.neighborhood,
        public_area=location.public_area,
        state=location.state,
    )


def inventory_response(inventory: ListingInventory | None) -> ListingInventoryResponse | None:
    if inventory is None:
        return None
    return ListingInventoryResponse(
        quantity_available=inventory.quantity_available,
        quantity_total=inventory.quantity_total,
    )


def image_response(image: ListingImage) -> ListingImageResponse:
    public_url = image.media_asset.public_url if image.media_asset.status == "approved" else None
    return ListingImageResponse(
        alt_text=image.alt_text,
        id=image.public_id,
        is_primary=image.is_primary,
        media=media_response(image.media_asset),
        public_url=public_url,
        sort_order=image.sort_order,
    )


def media_response(media: MediaAsset) -> MediaAssetResponse:
    public_url = media.public_url if media.status == "approved" else None
    return MediaAssetResponse(
        byte_size=media.byte_size,
        content_type=media.content_type,
        created_at=media.created_at,
        id=media.public_id,
        original_filename=media.original_filename,
        public_url=public_url,
        status=cast("MediaStatus", media.status),
    )


def sanitize_filename(filename: str) -> str:
    cleaned = _SAFE_FILENAME.sub("-", filename.strip()).strip(".-")
    return cleaned or "upload"


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
