from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import CurrentPrincipal, get_current_principal
from oldpages_api.recommendations.schemas import (
    ConditionSuggestionResponse,
    DismissRecommendationRequest,
    FeedbackRequest,
    FeedbackResponse,
    FraudPriorityResponse,
    ListingDescriptionSuggestionResponse,
    RecommendationFilters,
    RecommendationListResponse,
)
from oldpages_api.recommendations.service import RecommendationService
from oldpages_api.shared.db.database import get_session

recommendations_router = APIRouter(prefix="/recommendations", tags=["recommendations"])
listings_router = APIRouter(prefix="/listings", tags=["listings"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def _service(session: AsyncSession) -> RecommendationService:
    return RecommendationService(session)


@recommendations_router.get("", response_model=RecommendationListResponse)
async def get_my_recommendations(
    principal: PrincipalDep,
    session: SessionDep,
    entity_type: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> RecommendationListResponse:
    filters = RecommendationFilters(
        entity_type=entity_type,  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        limit=limit,
        cursor=cursor,
    )
    return await _service(session).get_my_recommendations(filters, principal.user)


@recommendations_router.post(
    "/{rec_id}/dismiss",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def dismiss_recommendation(
    rec_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> None:
    await _service(session).dismiss_recommendation(
        rec_id,
        DismissRecommendationRequest(),
        principal.user,
    )


@recommendations_router.post("/{rec_id}/click", status_code=status.HTTP_204_NO_CONTENT)
async def record_click(
    rec_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> None:
    await _service(session).record_click(rec_id, principal.user)


@recommendations_router.post("/{rec_id}/feedback", response_model=FeedbackResponse)
async def record_feedback(
    rec_id: str,
    payload: FeedbackRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> FeedbackResponse:
    return await _service(session).record_feedback(rec_id, payload, principal.user)


@recommendations_router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh_recommendations(
    principal: PrincipalDep,
    session: SessionDep,
) -> None:
    await _service(session).refresh_recommendations(principal.user)


@recommendations_router.get("/price-suggestion")
async def get_price_suggestion(
    session: SessionDep,
    book_id: int = Query(...),
    condition: str = Query(...),
) -> dict[str, Any]:
    return await _service(session).get_price_suggestion(book_id, condition)


@recommendations_router.get("/category-suggestions")
async def suggest_categories(
    session: SessionDep,
    title: str = Query(default=""),
    description: str = Query(default=""),
) -> dict[str, list[str]]:
    slugs = await _service(session).suggest_categories(title, description)
    return {"categories": slugs}


@recommendations_router.get(
    "/condition-suggestion",
    response_model=ConditionSuggestionResponse,
)
async def suggest_condition(
    session: SessionDep,
    title: str = Query(default=""),
    description: str = Query(default=""),
) -> ConditionSuggestionResponse:
    return await _service(session).suggest_condition(title, description)


@recommendations_router.get(
    "/listing-description",
    response_model=ListingDescriptionSuggestionResponse,
)
async def suggest_listing_description(
    session: SessionDep,
    title: str = Query(default=""),
    condition: str = Query(default="good"),
    notes: str = Query(default=""),
) -> ListingDescriptionSuggestionResponse:
    return await _service(session).suggest_listing_description(title, condition, notes)


@recommendations_router.get(
    "/fraud-priority",
    response_model=FraudPriorityResponse,
)
async def prioritize_fraud_review(
    session: SessionDep,
    title: str = Query(default=""),
    description: str = Query(default=""),
    price_amount_cents: int | None = Query(default=None, ge=0),
) -> FraudPriorityResponse:
    return await _service(session).prioritize_fraud_review(
        title,
        description,
        price_amount_cents,
    )


@listings_router.get("/{listing_id}/similar", response_model=list[dict[str, Any]])
async def get_similar_listings(
    listing_id: int,
    session: SessionDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict[str, Any]]:
    listings = await _service(session).get_similar_listings(listing_id, limit)
    return [
        {
            "id": listing.public_id,
            "title": listing.title_snapshot,
            "price_amount_cents": listing.price_amount_cents,
        }
        for listing in listings
    ]
