from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from oldpages_api.listings.schemas import (
    ConditionGrade,
    DeliveryMethod,
    ListingLocationPublicResponse,
    ListingMode,
)

SearchSort = Literal[
    "relevance",
    "nearest",
    "newest",
    "lowest_price",
    "highest_price",
    "best_condition",
    "most_saved",
]
SuggestionType = Literal["title", "author", "isbn", "category", "location"]
FollowTargetType = Literal["user", "seller", "author", "genre", "community", "college"]


class ListingSearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actual_photos: bool | None = None
    author: str | None = Field(default=None, max_length=240)
    campus_pickup: bool | None = None
    category: str | None = Field(default=None, max_length=180)
    city: str | None = Field(default=None, max_length=120)
    condition: ConditionGrade | None = None
    country: str | None = Field(default=None, max_length=80)
    cursor: str | None = Field(default=None, max_length=256)
    delivery_method: DeliveryMethod | None = None
    distance_km: float | None = Field(default=None, gt=0, le=500)
    first_edition: bool | None = None
    format: str | None = Field(default=None, max_length=32)
    free_only: bool = False
    isbn: str | None = Field(default=None, max_length=32)
    language: str | None = Field(default=None, max_length=24)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    limit: int = Field(default=20, ge=1, le=50)
    listing_mode: ListingMode | None = None
    longitude: float | None = Field(default=None, ge=-180, le=180)
    max_price_amount_cents: int | None = Field(default=None, ge=0)
    min_price_amount_cents: int | None = Field(default=None, ge=0)
    negotiable: bool | None = None
    publication_year: int | None = Field(default=None, ge=1450, le=2200)
    publisher: str | None = Field(default=None, max_length=240)
    q: str | None = Field(default=None, max_length=500)
    signed_copy: bool | None = None
    sort: SearchSort = "relevance"
    state: str | None = Field(default=None, max_length=120)

    @field_validator(
        "author",
        "category",
        "city",
        "country",
        "format",
        "isbn",
        "language",
        "publisher",
        "q",
        "state",
    )
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_location_sort(self) -> ListingSearchFilters:
        has_origin = self.latitude is not None and self.longitude is not None
        if self.sort == "nearest" and not has_origin:
            raise ValueError("latitude and longitude are required for nearest sorting.")
        if self.distance_km is not None and not has_origin:
            raise ValueError("latitude and longitude are required for distance filtering.")
        if self.min_price_amount_cents is not None and self.max_price_amount_cents is not None:
            if self.min_price_amount_cents > self.max_price_amount_cents:
                raise ValueError("min_price_amount_cents cannot exceed max_price_amount_cents.")
        return self

    def log_filters(self) -> dict[str, Any]:
        return self.model_dump(exclude={"cursor"}, exclude_none=True)


class SearchListingBookSummary(BaseModel):
    authors: list[str]
    categories: list[str]
    id: str
    isbn_10: str | None = None
    isbn_13: str | None = None
    title: str


class ListingSearchResult(BaseModel):
    book: SearchListingBookSummary
    condition: ConditionGrade | None
    created_at: datetime
    currency: str
    delivery_methods: list[DeliveryMethod]
    distance_km: float | None = None
    favorite_count: int
    id: str
    image_url: str | None = None
    listing_modes: list[ListingMode]
    location: ListingLocationPublicResponse | None
    negotiable: bool
    price_amount_cents: int | None = None
    quality_score: int
    seller: dict[str, str]
    title: str


class ListingSearchResponse(BaseModel):
    items: list[ListingSearchResult]
    next_cursor: str | None = None
    result_count: int


class SearchSuggestion(BaseModel):
    text: str
    type: SuggestionType


class SearchSuggestionResponse(BaseModel):
    items: list[SearchSuggestion]


class SavedSearchCreateRequest(BaseModel):
    filters: dict[str, Any] = Field(default_factory=dict)
    name: str = Field(min_length=1, max_length=120)
    notifications_enabled: bool = True
    query: str | None = Field(default=None, max_length=500)
    sort: SearchSort = "relevance"

    @field_validator("name", "query")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_name(self) -> SavedSearchCreateRequest:
        if self.name is None:
            raise ValueError("name is required.")
        return self


class SavedSearchResponse(BaseModel):
    created_at: datetime
    filters: dict[str, Any]
    id: str
    last_matched_at: datetime | None = None
    last_result_count: int
    name: str
    notifications_enabled: bool
    query: str | None = None
    sort: SearchSort


class SavedSearchListResponse(BaseModel):
    items: list[SavedSearchResponse]


class WishlistItemResponse(BaseModel):
    book: SearchListingBookSummary
    created_at: datetime
    id: str


class ListingFavoriteResponse(BaseModel):
    created_at: datetime
    id: str
    listing_id: str


class FollowCreateRequest(BaseModel):
    target_id: str = Field(min_length=1, max_length=180)
    target_label: str | None = Field(default=None, max_length=240)
    target_type: FollowTargetType

    @field_validator("target_id", "target_label")
    @classmethod
    def strip_target_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class FollowResponse(BaseModel):
    created_at: datetime
    id: str
    target_id: str
    target_label: str | None = None
    target_type: FollowTargetType
