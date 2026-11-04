from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from oldpages_api.catalog.exceptions import InvalidIsbnError

if False:  # pragma: no cover
    from oldpages_api.catalog.models import BookEdition
    from oldpages_api.catalog.repository import CatalogRepository

_ISBN_CLEANUP = re.compile(r"[\s-]+")


@dataclass(frozen=True, slots=True)
class NormalizedIsbn:
    identifier_type: str
    value: str


@dataclass(frozen=True, slots=True)
class IsbnLookupResult:
    book_edition: BookEdition | None
    isbn: NormalizedIsbn
    provider: str


class IsbnMetadataProvider(Protocol):
    async def resolve(
        self,
        repository: CatalogRepository,
        isbn: str,
    ) -> IsbnLookupResult: ...


class LocalCatalogIsbnProvider:
    provider = "local_catalog"

    async def resolve(
        self,
        repository: CatalogRepository,
        isbn: str,
    ) -> IsbnLookupResult:
        normalized = normalize_isbn(isbn)
        edition = await repository.get_edition_by_identifier(
            normalized.identifier_type,
            normalized.value,
        )
        return IsbnLookupResult(
            book_edition=edition,
            isbn=normalized,
            provider=self.provider,
        )


def normalize_isbn(value: str) -> NormalizedIsbn:
    cleaned = _ISBN_CLEANUP.sub("", value.strip()).upper()
    if len(cleaned) == 10 and _valid_isbn10(cleaned):
        return NormalizedIsbn(identifier_type="isbn10", value=cleaned)
    if len(cleaned) == 13 and _valid_isbn13(cleaned):
        return NormalizedIsbn(identifier_type="isbn13", value=cleaned)
    raise InvalidIsbnError()


def normalize_expected_isbn(value: str, expected_type: str) -> str:
    normalized = normalize_isbn(value)
    if normalized.identifier_type != expected_type:
        raise InvalidIsbnError()
    return normalized.value


def _valid_isbn10(value: str) -> bool:
    if not re.fullmatch(r"\d{9}[\dX]", value):
        return False
    total = 0
    for index, character in enumerate(value):
        digit = 10 if character == "X" else int(character)
        total += digit * (10 - index)
    return total % 11 == 0


def _valid_isbn13(value: str) -> bool:
    if not value.isdigit():
        return False
    total = 0
    for index, character in enumerate(value):
        multiplier = 1 if index % 2 == 0 else 3
        total += int(character) * multiplier
    return total % 10 == 0
