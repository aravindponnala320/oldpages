from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EntityType = Literal["book", "listing", "seller", "community", "event", "club"]
RecommendationSource = Literal[
    "reading_history",
    "wishlist",
    "search_history",
    "community",
    "location",
    "similar_users",
    "genre",
    "trending",
]
FeedbackType = Literal["helpful", "not_helpful", "not_interested", "already_have"]


class RecommendationResponse(BaseModel):
    confidence: float
    entity_id: int
    entity_type: EntityType
    id: str
    is_dismissed: bool
    model: str
    model_version: str
    provider: str
    reason: str
    score: float
    source: RecommendationSource


class RecommendationListResponse(BaseModel):
    items: list[RecommendationResponse]
    next_cursor: str | None = None


class DismissRecommendationRequest(BaseModel):
    pass


class FeedbackRequest(BaseModel):
    feedback_type: FeedbackType


class FeedbackResponse(BaseModel):
    created_at: datetime
    feedback_type: FeedbackType


class RecommendationFilters(BaseModel):
    entity_type: EntityType | None = None
    limit: int = Field(default=20, ge=1, le=100)
    source: RecommendationSource | None = None
    cursor: str | None = None


class AssistanceMetadata(BaseModel):
    confidence: float
    editable: bool = True
    human_confirmation_required: bool = True
    model: str
    model_version: str
    provider: str


class ConditionSuggestionResponse(AssistanceMetadata):
    alternatives: list[str]
    explanation: str
    suggested_condition: str


class ListingDescriptionSuggestionResponse(AssistanceMetadata):
    suggested_description: str
    unsupported_metadata_warning: str | None = None


ReviewPriority = Literal["low", "medium", "high"]


class FraudPriorityResponse(AssistanceMetadata):
    auto_action_allowed: bool = False
    priority: ReviewPriority
    reasons: list[str]
    review_only: bool = True
