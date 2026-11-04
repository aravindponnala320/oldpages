from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from oldpages_api.catalog.isbn import normalize_expected_isbn, normalize_isbn

BookFormat = Literal[
    "paperback",
    "hardcover",
    "ebook",
    "audiobook",
    "spiral_bound",
    "loose_leaf",
    "unknown",
]
IdentifierType = Literal["isbn10", "isbn13", "open_library", "google_books", "other"]
MetadataStatus = Literal["needs_review", "verified"]
AuthorRole = Literal["author", "editor", "translator", "illustrator", "contributor"]


class AuthorInput(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    role: AuthorRole = "author"

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return " ".join(value.strip().split())


class PublisherInput(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    website_url: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return " ".join(value.strip().split())


class BookIdentifierInput(BaseModel):
    identifier_type: IdentifierType
    identifier_value: str = Field(min_length=1, max_length=120)
    source: str = Field(default="manual", min_length=1, max_length=80)

    @field_validator("identifier_value")
    @classmethod
    def normalize_identifier_value(cls, value: str) -> str:
        return value.strip()


class AcademicMetadataInput(BaseModel):
    school_board: str | None = Field(default=None, max_length=120)
    grade: str | None = Field(default=None, max_length=40)
    subject: str | None = Field(default=None, max_length=160)
    college: str | None = Field(default=None, max_length=180)
    university: str | None = Field(default=None, max_length=180)
    degree: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=160)
    course: str | None = Field(default=None, max_length=160)
    semester: str | None = Field(default=None, max_length=40)
    professor: str | None = Field(default=None, max_length=160)
    exam: str | None = Field(default=None, max_length=160)
    exam_year: int | None = Field(default=None, ge=1800, le=2200)
    syllabus_version: str | None = Field(default=None, max_length=80)


class BookCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    subtitle: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=8000)
    authors: list[AuthorInput] = Field(min_length=1, max_length=20)
    publisher: PublisherInput | None = None
    isbn_10: str | None = Field(default=None, max_length=32)
    isbn_13: str | None = Field(default=None, max_length=32)
    identifiers: list[BookIdentifierInput] = Field(default_factory=list, max_length=20)
    edition: str | None = Field(default=None, max_length=120)
    publication_year: int | None = Field(default=None, ge=1450, le=2200)
    language: str = Field(default="en", min_length=2, max_length=24)
    page_count: int | None = Field(default=None, gt=0)
    format: BookFormat = "unknown"
    cover_image_url: str | None = Field(default=None, max_length=1000)
    category_ids: list[str] = Field(default_factory=list, max_length=20)
    genres: list[str] = Field(default_factory=list, max_length=30)
    subjects: list[str] = Field(default_factory=list, max_length=30)
    academic_metadata: AcademicMetadataInput | None = None

    @field_validator("isbn_10")
    @classmethod
    def normalize_isbn10(cls, value: str | None) -> str | None:
        return normalize_expected_isbn(value, "isbn10") if value else None

    @field_validator("isbn_13")
    @classmethod
    def normalize_isbn13(cls, value: str | None) -> str | None:
        return normalize_expected_isbn(value, "isbn13") if value else None

    @field_validator("language", "format")
    @classmethod
    def normalize_lowercase(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("genres", "subjects")
    @classmethod
    def normalize_string_list(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            cleaned = " ".join(item.strip().split())
            key = cleaned.casefold()
            if cleaned and key not in seen:
                seen.add(key)
                normalized.append(cleaned)
        return normalized


class BookUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    subtitle: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=8000)
    authors: list[AuthorInput] | None = Field(default=None, min_length=1, max_length=20)
    publisher: PublisherInput | None = None
    isbn_10: str | None = Field(default=None, max_length=32)
    isbn_13: str | None = Field(default=None, max_length=32)
    identifiers: list[BookIdentifierInput] | None = Field(default=None, max_length=20)
    edition: str | None = Field(default=None, max_length=120)
    publication_year: int | None = Field(default=None, ge=1450, le=2200)
    language: str | None = Field(default=None, min_length=2, max_length=24)
    page_count: int | None = Field(default=None, gt=0)
    format: BookFormat | None = None
    cover_image_url: str | None = Field(default=None, max_length=1000)
    category_ids: list[str] | None = Field(default=None, max_length=20)
    genres: list[str] | None = Field(default=None, max_length=30)
    subjects: list[str] | None = Field(default=None, max_length=30)
    academic_metadata: AcademicMetadataInput | None = None
    metadata_status: MetadataStatus | None = None

    @field_validator("isbn_10")
    @classmethod
    def normalize_isbn10(cls, value: str | None) -> str | None:
        return normalize_expected_isbn(value, "isbn10") if value else None

    @field_validator("isbn_13")
    @classmethod
    def normalize_isbn13(cls, value: str | None) -> str | None:
        return normalize_expected_isbn(value, "isbn13") if value else None

    @field_validator("language", "format")
    @classmethod
    def normalize_lowercase(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else value

    @field_validator("genres", "subjects")
    @classmethod
    def normalize_string_list(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return BookCreateRequest.normalize_string_list(value)


class ResolveIsbnRequest(BaseModel):
    isbn: str = Field(min_length=10, max_length=32)

    @field_validator("isbn")
    @classmethod
    def normalize_isbn_value(cls, value: str) -> str:
        return normalize_isbn(value).value


class AuthorSummary(BaseModel):
    id: str
    name: str
    role: AuthorRole = "author"


class PublisherSummary(BaseModel):
    id: str
    name: str
    website_url: str | None = None


class CategorySummary(BaseModel):
    id: str
    name: str
    parent_id: str | None = None
    slug: str


class BookIdentifierResponse(BaseModel):
    identifier_type: IdentifierType
    identifier_value: str
    source: str


class AcademicMetadataResponse(BaseModel):
    school_board: str | None = None
    grade: str | None = None
    subject: str | None = None
    college: str | None = None
    university: str | None = None
    degree: str | None = None
    department: str | None = None
    course: str | None = None
    semester: str | None = None
    professor: str | None = None
    exam: str | None = None
    exam_year: int | None = None
    syllabus_version: str | None = None


class BookResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    academic_metadata: AcademicMetadataResponse | None = None
    authors: list[AuthorSummary]
    categories: list[CategorySummary]
    cover_image_url: str | None = None
    created_at: datetime
    description: str | None = None
    edition: str | None = None
    format: BookFormat
    genres: list[str]
    id: str
    identifiers: list[BookIdentifierResponse]
    isbn_10: str | None = None
    isbn_13: str | None = None
    language: str
    metadata_status: MetadataStatus
    page_count: int | None = None
    publication_year: int | None = None
    publisher: PublisherSummary | None = None
    subjects: list[str]
    subtitle: str | None = None
    title: str
    updated_at: datetime
    work_id: str


class BookListResponse(BaseModel):
    items: list[BookResponse]
    next_cursor: str | None = None


class ResolveIsbnResponse(BaseModel):
    book: BookResponse | None = None
    isbn: str
    provider: str
    status: Literal["found", "not_found"]


class CategoryNode(BaseModel):
    children: list[CategoryNode] = Field(default_factory=list)
    id: str
    name: str
    parent_id: str | None = None
    slug: str


class CategoryTreeResponse(BaseModel):
    items: list[CategoryNode]


class AuthorListResponse(BaseModel):
    items: list[AuthorSummary]
    next_cursor: str | None = None


class PublisherListResponse(BaseModel):
    items: list[PublisherSummary]
    next_cursor: str | None = None


CategoryNode.model_rebuild()
