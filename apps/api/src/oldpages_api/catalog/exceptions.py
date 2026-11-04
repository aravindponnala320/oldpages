from __future__ import annotations

from oldpages_api.core.errors import AppError


class CatalogEntryNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Catalog entry not found.",
            status_code=404,
            title="Catalog Entry Not Found",
            type_uri="https://oldpages.in/problems/catalog-entry-not-found",
        )


class CategoryNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Category not found.",
            status_code=404,
            title="Category Not Found",
            type_uri="https://oldpages.in/problems/category-not-found",
        )


class DuplicateCatalogEntryError(AppError):
    def __init__(self, existing_book_id: str) -> None:
        super().__init__(
            detail="A catalog edition with matching metadata already exists.",
            extra={"existing_book_id": existing_book_id},
            status_code=409,
            title="Duplicate Catalog Entry",
            type_uri="https://oldpages.in/problems/duplicate-catalog-entry",
        )


class ForbiddenCatalogActionError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="This catalog action is not allowed.",
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


class InvalidIsbnError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="ISBN must be a valid ISBN-10 or ISBN-13 value.",
            status_code=422,
            title="Invalid ISBN",
            type_uri="https://oldpages.in/problems/invalid-isbn",
        )
