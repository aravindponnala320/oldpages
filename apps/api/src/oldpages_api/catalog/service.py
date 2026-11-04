from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.catalog.events import BOOK_CATALOG_CREATED, BOOK_CATALOG_UPDATED
from oldpages_api.catalog.exceptions import (
    CatalogEntryNotFoundError,
    CategoryNotFoundError,
    DuplicateCatalogEntryError,
)
from oldpages_api.catalog.isbn import (
    IsbnMetadataProvider,
    LocalCatalogIsbnProvider,
    normalize_expected_isbn,
    normalize_isbn,
)
from oldpages_api.catalog.models import (
    AcademicMetadata,
    Author,
    Book,
    BookAuthor,
    BookCategory,
    BookEdition,
    BookIdentifier,
    Category,
    Publisher,
)
from oldpages_api.catalog.permissions import require_catalog_manager
from oldpages_api.catalog.repository import CatalogRepository
from oldpages_api.catalog.schemas import (
    AcademicMetadataInput,
    AcademicMetadataResponse,
    AuthorInput,
    AuthorListResponse,
    AuthorRole,
    AuthorSummary,
    BookCreateRequest,
    BookFormat,
    BookIdentifierInput,
    BookIdentifierResponse,
    BookListResponse,
    BookResponse,
    BookUpdateRequest,
    CategoryNode,
    CategorySummary,
    CategoryTreeResponse,
    IdentifierType,
    MetadataStatus,
    PublisherInput,
    PublisherListResponse,
    PublisherSummary,
    ResolveIsbnResponse,
)
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext


@dataclass(frozen=True, slots=True)
class IdentifierPair:
    identifier_type: str
    identifier_value: str
    source: str


class CatalogService:
    def __init__(
        self,
        session: AsyncSession,
        isbn_provider: IsbnMetadataProvider | None = None,
    ) -> None:
        self.repo = CatalogRepository(session)
        self.session = session
        self.isbn_provider = isbn_provider or LocalCatalogIsbnProvider()

    async def list_books(
        self,
        *,
        author: str | None,
        category: str | None,
        cursor: str | None,
        isbn: str | None,
        language: str | None,
        limit: int,
        publisher: str | None,
        query: str | None,
    ) -> BookListResponse:
        identifier = None
        if isbn:
            normalized_isbn = normalize_isbn(isbn)
            identifier = (normalized_isbn.identifier_type, normalized_isbn.value)

        category_model = None
        if category:
            category_model = await self.repo.get_category_by_public_id_or_slug(category)
            if category_model is None:
                return BookListResponse(items=[], next_cursor=None)

        editions, next_cursor = await self.repo.list_book_editions(
            author=author,
            category=category_model,
            cursor=cursor,
            identifier=identifier,
            language=language,
            limit=limit,
            publisher=publisher,
            query=query,
        )
        return BookListResponse(
            items=[self.book_response(edition) for edition in editions],
            next_cursor=next_cursor,
        )

    async def get_book(self, book_id: str) -> BookResponse:
        edition = await self.repo.get_edition_by_public_id(book_id)
        if edition is None:
            raise CatalogEntryNotFoundError()
        return self.book_response(edition)

    async def resolve_isbn(self, isbn: str) -> ResolveIsbnResponse:
        result = await self.isbn_provider.resolve(self.repo, isbn)
        if result.book_edition is None:
            return ResolveIsbnResponse(
                book=None,
                isbn=result.isbn.value,
                provider=result.provider,
                status="not_found",
            )
        return ResolveIsbnResponse(
            book=self.book_response(result.book_edition),
            isbn=result.isbn.value,
            provider=result.provider,
            status="found",
        )

    async def create_book(
        self,
        payload: BookCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> BookResponse:
        require_catalog_manager(actor)
        identifiers = self.identifier_pairs_from_create(payload)
        await self.ensure_unique_identifiers(identifiers)

        authors = await self.author_models(payload.authors)
        publisher = await self.publisher_model(payload.publisher)
        categories = await self.category_models(payload.category_ids)
        fingerprint = edition_fingerprint(
            title=payload.title,
            authors=[author.normalized_name for author, _role in authors],
            edition=payload.edition,
            format=payload.format,
            language=payload.language,
            publication_year=payload.publication_year,
            publisher=publisher.normalized_name if publisher else None,
        )
        existing = await self.repo.get_edition_by_fingerprint(fingerprint)
        if existing is not None:
            raise DuplicateCatalogEntryError(existing.public_id)

        book = Book(
            description=payload.description,
            normalized_title=normalize_name(payload.title),
            original_language=payload.language,
            subtitle=payload.subtitle,
            title=payload.title,
        )
        self.repo.add(book)
        await self.repo.flush()

        for position, (author, role) in enumerate(authors):
            self.repo.add(
                BookAuthor(
                    author_id=author.id,
                    book_id=book.id,
                    position=position,
                    role=role,
                )
            )
        for category in categories:
            self.repo.add(BookCategory(book_id=book.id, category_id=category.id))

        edition = BookEdition(
            book_id=book.id,
            cover_image_url=payload.cover_image_url,
            description=payload.description,
            edition=payload.edition,
            edition_fingerprint=fingerprint,
            format=payload.format,
            genres=payload.genres,
            language=payload.language,
            metadata_status="needs_review",
            page_count=payload.page_count,
            publication_year=payload.publication_year,
            publisher_id=publisher.id if publisher else None,
            subjects=payload.subjects,
            subtitle=payload.subtitle,
            title=payload.title,
        )
        self.repo.add(edition)
        await self.repo.flush()

        for identifier in identifiers:
            self.repo.add(
                BookIdentifier(
                    book_edition_id=edition.id,
                    identifier_type=identifier.identifier_type,
                    identifier_value=identifier.identifier_value,
                    source=identifier.source,
                )
            )

        academic_metadata = build_academic_metadata(payload.academic_metadata, edition.id)
        if academic_metadata is not None:
            self.repo.add(academic_metadata)

        await self.audit(
            action=BOOK_CATALOG_CREATED,
            actor=actor,
            context=context,
            payload={"book_id": edition.public_id, "title": edition.title},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_edition_by_public_id(edition.public_id)
        if reloaded is None:
            raise CatalogEntryNotFoundError()
        return self.book_response(reloaded)

    async def update_book(
        self,
        book_id: str,
        payload: BookUpdateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> BookResponse:
        require_catalog_manager(actor)
        edition = await self.repo.get_edition_by_public_id(book_id)
        if edition is None:
            raise CatalogEntryNotFoundError()

        fields = payload.model_fields_set
        if "title" in fields and payload.title is not None:
            edition.title = payload.title
            edition.book.title = payload.title
            edition.book.normalized_title = normalize_name(payload.title)
        if "subtitle" in fields:
            edition.subtitle = payload.subtitle
            edition.book.subtitle = payload.subtitle
        if "description" in fields:
            edition.description = payload.description
            edition.book.description = payload.description
        if "edition" in fields:
            edition.edition = payload.edition
        if "publication_year" in fields:
            edition.publication_year = payload.publication_year
        if "language" in fields and payload.language is not None:
            edition.language = payload.language
            edition.book.original_language = payload.language
        if "page_count" in fields:
            edition.page_count = payload.page_count
        if "format" in fields and payload.format is not None:
            edition.format = payload.format
        if "cover_image_url" in fields:
            edition.cover_image_url = payload.cover_image_url
        if "genres" in fields and payload.genres is not None:
            edition.genres = payload.genres
        if "subjects" in fields and payload.subjects is not None:
            edition.subjects = payload.subjects
        if "metadata_status" in fields and payload.metadata_status is not None:
            edition.metadata_status = payload.metadata_status

        if "publisher" in fields:
            publisher = await self.publisher_model(payload.publisher)
            edition.publisher = publisher
            edition.publisher_id = publisher.id if publisher else None

        if "authors" in fields and payload.authors is not None:
            authors = await self.author_models(payload.authors)
            edition.book.authors.clear()
            await self.repo.flush()
            for position, (author, role) in enumerate(authors):
                self.repo.add(
                    BookAuthor(
                        author=author,
                        book=edition.book,
                        position=position,
                        role=role,
                    )
                )

        if "category_ids" in fields and payload.category_ids is not None:
            categories = await self.category_models(payload.category_ids)
            edition.book.categories.clear()
            await self.repo.flush()
            for category in categories:
                self.repo.add(BookCategory(book_id=edition.book.id, category_id=category.id))

        if identifier_fields_present(fields):
            identifiers = self.identifier_pairs_from_update(payload, edition)
            await self.ensure_unique_identifiers(identifiers, except_edition_id=edition.id)
            edition.identifiers.clear()
            await self.repo.flush()
            for identifier in identifiers:
                self.repo.add(
                    BookIdentifier(
                        book_edition_id=edition.id,
                        identifier_type=identifier.identifier_type,
                        identifier_value=identifier.identifier_value,
                        source=identifier.source,
                    )
                )

        if "academic_metadata" in fields:
            if edition.academic_metadata is not None:
                await self.session.delete(edition.academic_metadata)
                edition.academic_metadata = None
                await self.repo.flush()
            academic_metadata = build_academic_metadata(payload.academic_metadata, edition.id)
            if academic_metadata is not None:
                self.repo.add(academic_metadata)

        fingerprint = edition_fingerprint(
            title=edition.title,
            authors=[book_author.author.normalized_name for book_author in edition.book.authors],
            edition=edition.edition,
            format=edition.format,
            language=edition.language,
            publication_year=edition.publication_year,
            publisher=edition.publisher.normalized_name if edition.publisher else None,
        )
        existing = await self.repo.get_edition_by_fingerprint(fingerprint)
        if existing is not None and existing.id != edition.id:
            raise DuplicateCatalogEntryError(existing.public_id)
        edition.edition_fingerprint = fingerprint

        await self.audit(
            action=BOOK_CATALOG_UPDATED,
            actor=actor,
            context=context,
            payload={"book_id": edition.public_id, "title": edition.title},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_edition_by_public_id(edition.public_id)
        if reloaded is None:
            raise CatalogEntryNotFoundError()
        return self.book_response(reloaded)

    async def list_categories(self) -> CategoryTreeResponse:
        categories = await self.repo.list_categories()
        return CategoryTreeResponse(items=category_tree(categories))

    async def list_authors(
        self,
        *,
        cursor: str | None,
        limit: int,
        query: str | None,
    ) -> AuthorListResponse:
        authors, next_cursor = await self.repo.list_authors(
            cursor=cursor,
            limit=limit,
            query=query,
        )
        return AuthorListResponse(
            items=[
                AuthorSummary(id=author.public_id, name=author.name, role="author")
                for author in authors
            ],
            next_cursor=next_cursor,
        )

    async def list_publishers(
        self,
        *,
        cursor: str | None,
        limit: int,
        query: str | None,
    ) -> PublisherListResponse:
        publishers, next_cursor = await self.repo.list_publishers(
            cursor=cursor,
            limit=limit,
            query=query,
        )
        return PublisherListResponse(
            items=[
                PublisherSummary(
                    id=publisher.public_id,
                    name=publisher.name,
                    website_url=publisher.website_url,
                )
                for publisher in publishers
            ],
            next_cursor=next_cursor,
        )

    async def author_models(self, authors: list[AuthorInput]) -> list[tuple[Author, str]]:
        models: list[tuple[Author, str]] = []
        seen: set[tuple[str, str]] = set()
        for author_input in authors:
            normalized_name = normalize_name(author_input.name)
            key = (normalized_name, author_input.role)
            if key in seen:
                continue
            seen.add(key)
            author = await self.repo.get_or_create_author(author_input.name, normalized_name)
            models.append((author, author_input.role))
        return models

    async def publisher_model(self, publisher: PublisherInput | None) -> Publisher | None:
        if publisher is None:
            return None
        return await self.repo.get_or_create_publisher(
            name=publisher.name,
            normalized_name=normalize_name(publisher.name),
            website_url=publisher.website_url,
        )

    async def category_models(self, category_ids: list[str]) -> list[Category]:
        categories: list[Category] = []
        seen: set[int] = set()
        for category_id in category_ids:
            category = await self.repo.get_category_by_public_id_or_slug(category_id)
            if category is None or not category.is_active:
                raise CategoryNotFoundError()
            if category.id not in seen:
                seen.add(category.id)
                categories.append(category)
        return categories

    async def ensure_unique_identifiers(
        self,
        identifiers: list[IdentifierPair],
        *,
        except_edition_id: int | None = None,
    ) -> None:
        for identifier in identifiers:
            existing = await self.repo.get_edition_by_identifier(
                identifier.identifier_type,
                identifier.identifier_value,
            )
            if existing is not None and existing.id != except_edition_id:
                raise DuplicateCatalogEntryError(existing.public_id)

    def identifier_pairs_from_create(self, payload: BookCreateRequest) -> list[IdentifierPair]:
        identifiers: list[IdentifierPair] = []
        if payload.isbn_10:
            identifiers.append(IdentifierPair("isbn10", payload.isbn_10, "manual"))
        if payload.isbn_13:
            identifiers.append(IdentifierPair("isbn13", payload.isbn_13, "manual"))
        identifiers.extend(identifier_pair_from_input(item) for item in payload.identifiers)
        return dedupe_identifiers(identifiers)

    def identifier_pairs_from_update(
        self,
        payload: BookUpdateRequest,
        edition: BookEdition,
    ) -> list[IdentifierPair]:
        current = {
            identifier.identifier_type: IdentifierPair(
                identifier.identifier_type,
                identifier.identifier_value,
                identifier.source,
            )
            for identifier in edition.identifiers
            if identifier.identifier_type in {"isbn10", "isbn13"}
        }
        if "isbn_10" in payload.model_fields_set:
            if payload.isbn_10 is None:
                current.pop("isbn10", None)
            else:
                current["isbn10"] = IdentifierPair("isbn10", payload.isbn_10, "manual")
        if "isbn_13" in payload.model_fields_set:
            if payload.isbn_13 is None:
                current.pop("isbn13", None)
            else:
                current["isbn13"] = IdentifierPair("isbn13", payload.isbn_13, "manual")

        identifiers = list(current.values())
        if "identifiers" in payload.model_fields_set and payload.identifiers is not None:
            identifiers.extend(identifier_pair_from_input(item) for item in payload.identifiers)
        else:
            identifiers.extend(
                IdentifierPair(
                    identifier.identifier_type,
                    identifier.identifier_value,
                    identifier.source,
                )
                for identifier in edition.identifiers
                if identifier.identifier_type not in {"isbn10", "isbn13"}
            )
        return dedupe_identifiers(identifiers)

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

    def book_response(self, edition: BookEdition) -> BookResponse:
        identifiers = sorted(
            edition.identifiers,
            key=lambda item: (item.identifier_type, item.identifier_value),
        )
        isbn_10 = next(
            (
                identifier.identifier_value
                for identifier in identifiers
                if identifier.identifier_type == "isbn10"
            ),
            None,
        )
        isbn_13 = next(
            (
                identifier.identifier_value
                for identifier in identifiers
                if identifier.identifier_type == "isbn13"
            ),
            None,
        )
        return BookResponse(
            academic_metadata=academic_metadata_response(edition.academic_metadata),
            authors=[
                AuthorSummary(
                    id=book_author.author.public_id,
                    name=book_author.author.name,
                    role=cast("AuthorRole", book_author.role),
                )
                for book_author in sorted(edition.book.authors, key=lambda item: item.position)
            ],
            categories=[
                CategorySummary(
                    id=book_category.category.public_id,
                    name=book_category.category.name,
                    slug=book_category.category.slug,
                )
                for book_category in sorted(
                    edition.book.categories,
                    key=lambda item: (item.category.sort_order, item.category.name),
                )
            ],
            cover_image_url=edition.cover_image_url,
            created_at=edition.created_at,
            description=edition.description,
            edition=edition.edition,
            format=cast("BookFormat", edition.format),
            genres=edition.genres,
            id=edition.public_id,
            identifiers=[
                BookIdentifierResponse(
                    identifier_type=cast("IdentifierType", identifier.identifier_type),
                    identifier_value=identifier.identifier_value,
                    source=identifier.source,
                )
                for identifier in identifiers
            ],
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            language=edition.language,
            metadata_status=cast("MetadataStatus", edition.metadata_status),
            page_count=edition.page_count,
            publication_year=edition.publication_year,
            publisher=publisher_summary(edition.publisher),
            subjects=edition.subjects,
            subtitle=edition.subtitle,
            title=edition.title,
            updated_at=edition.updated_at,
            work_id=edition.book.public_id,
        )


def identifier_pair_from_input(identifier: BookIdentifierInput) -> IdentifierPair:
    if identifier.identifier_type in {"isbn10", "isbn13"}:
        return IdentifierPair(
            identifier.identifier_type,
            normalize_expected_isbn(identifier.identifier_value, identifier.identifier_type),
            identifier.source,
        )
    return IdentifierPair(
        identifier.identifier_type,
        identifier.identifier_value.strip(),
        identifier.source,
    )


def dedupe_identifiers(identifiers: list[IdentifierPair]) -> list[IdentifierPair]:
    deduped: list[IdentifierPair] = []
    seen: set[tuple[str, str]] = set()
    for identifier in identifiers:
        key = (identifier.identifier_type, identifier.identifier_value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(identifier)
    return deduped


def identifier_fields_present(fields: set[str]) -> bool:
    return bool({"isbn_10", "isbn_13", "identifiers"} & fields)


def build_academic_metadata(
    payload: AcademicMetadataInput | None,
    edition_id: int,
) -> AcademicMetadata | None:
    if payload is None:
        return None
    values = payload.model_dump()
    if not any(value is not None for value in values.values()):
        return None
    return AcademicMetadata(book_edition_id=edition_id, **values)


def academic_metadata_response(
    metadata: AcademicMetadata | None,
) -> AcademicMetadataResponse | None:
    if metadata is None:
        return None
    return AcademicMetadataResponse(
        school_board=metadata.school_board,
        grade=metadata.grade,
        subject=metadata.subject,
        college=metadata.college,
        university=metadata.university,
        degree=metadata.degree,
        department=metadata.department,
        course=metadata.course,
        semester=metadata.semester,
        professor=metadata.professor,
        exam=metadata.exam,
        exam_year=metadata.exam_year,
        syllabus_version=metadata.syllabus_version,
    )


def publisher_summary(publisher: Publisher | None) -> PublisherSummary | None:
    if publisher is None:
        return None
    return PublisherSummary(
        id=publisher.public_id,
        name=publisher.name,
        website_url=publisher.website_url,
    )


def category_tree(categories: list[Category]) -> list[CategoryNode]:
    nodes = {
        category.id: CategoryNode(
            id=category.public_id,
            name=category.name,
            parent_id=None,
            slug=category.slug,
        )
        for category in categories
    }
    roots: list[CategoryNode] = []
    for category in categories:
        node = nodes[category.id]
        if category.parent_id is None or category.parent_id not in nodes:
            roots.append(node)
            continue
        parent = nodes[category.parent_id]
        node.parent_id = parent.id
        parent.children.append(node)
    return roots


def edition_fingerprint(
    *,
    authors: list[str],
    edition: str | None,
    format: str,
    language: str,
    publication_year: int | None,
    publisher: str | None,
    title: str,
) -> str:
    raw = "|".join(
        [
            normalize_name(title),
            ",".join(authors),
            normalize_name(publisher or ""),
            normalize_name(edition or ""),
            str(publication_year or ""),
            language.strip().lower(),
            format.strip().lower(),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_name(value: str) -> str:
    return " ".join(value.strip().casefold().split())
