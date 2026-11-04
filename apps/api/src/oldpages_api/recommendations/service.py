from __future__ import annotations

import base64
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.models import User
from oldpages_api.listings.models import Listing
from oldpages_api.recommendations.engine import RecommendationEngine
from oldpages_api.recommendations.exceptions import (
    RecommendationNotFoundError,
)
from oldpages_api.recommendations.models import Recommendation, RecommendationFeedback
from oldpages_api.recommendations.permissions import require_recommendation_owner
from oldpages_api.recommendations.repository import RecommendationRepository
from oldpages_api.recommendations.schemas import (
    ConditionSuggestionResponse,
    DismissRecommendationRequest,
    FeedbackRequest,
    FeedbackResponse,
    FraudPriorityResponse,
    ListingDescriptionSuggestionResponse,
    RecommendationFilters,
    RecommendationListResponse,
    RecommendationResponse,
    ReviewPriority,
)

logger = logging.getLogger(__name__)

_STALE_THRESHOLD_HOURS = 24
ASSISTANCE_PROVIDER = "rules"
ASSISTANCE_MODEL = "oldpages-rule-engine"
ASSISTANCE_MODEL_VERSION = "1"


class RecommendationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = RecommendationRepository(session)
        self.engine = RecommendationEngine(session)
        self.session = session

    async def get_my_recommendations(
        self,
        filters: RecommendationFilters,
        actor: User,
    ) -> RecommendationListResponse:
        cursor_offset = _decode_cursor(filters.cursor)
        items = await self.repo.list_for_user(
            user_id=actor.id,
            entity_type=filters.entity_type,
            source=filters.source,
            limit=filters.limit + 1,
            cursor=cursor_offset,
        )
        has_more = len(items) > filters.limit
        page = items[: filters.limit]

        for item in page:
            await self.repo.mark_shown(item.id)
        await self.repo.commit()

        next_cursor: str | None = None
        if has_more:
            next_cursor = _encode_cursor(cursor_offset + filters.limit)

        return RecommendationListResponse(
            items=[_recommendation_response(r) for r in page],
            next_cursor=next_cursor,
        )

    async def dismiss_recommendation(
        self,
        recommendation_id: str,
        _payload: DismissRecommendationRequest,
        actor: User,
    ) -> None:
        rec = await self._get_recommendation(recommendation_id)
        require_recommendation_owner(rec, actor)
        rec.is_dismissed = True
        rec.dismissed_at = datetime.now(UTC)
        await self.repo.commit()

    async def record_feedback(
        self,
        recommendation_id: str,
        payload: FeedbackRequest,
        actor: User,
    ) -> FeedbackResponse:
        rec = await self._get_recommendation(recommendation_id)
        require_recommendation_owner(rec, actor)
        existing = await self.repo.get_feedback(actor.id, rec.id)
        if existing is not None:
            existing.feedback_type = payload.feedback_type
            await self.repo.commit()
            return FeedbackResponse(
                created_at=existing.created_at,
                feedback_type=payload.feedback_type,
            )
        feedback = RecommendationFeedback(
            feedback_type=payload.feedback_type,
            recommendation_id=rec.id,
            user_id=actor.id,
        )
        self.repo.add(feedback)
        await self.repo.flush()
        await self.repo.commit()
        return FeedbackResponse(
            created_at=feedback.created_at,
            feedback_type=payload.feedback_type,
        )

    async def record_click(
        self,
        recommendation_id: str,
        actor: User,
    ) -> None:
        rec = await self._get_recommendation(recommendation_id)
        require_recommendation_owner(rec, actor)
        await self.repo.mark_clicked(rec.id)
        await self.repo.commit()

    async def refresh_recommendations(self, actor: User) -> None:
        recs = await self.engine.generate_for_user(actor.id)
        for item in recs:
            await self.repo.upsert_recommendation(
                user_id=actor.id,
                entity_type=item["entity_type"],
                entity_id=item["entity_id"],
                score=item["score"],
                reason=item["reason"],
                source=item["source"],
            )
        await self.repo.commit()
        logger.info(
            "Refreshed %d recommendations for user %d",
            len(recs),
            actor.id,
        )

    async def get_price_suggestion(self, book_id: int, condition: str) -> dict[str, Any]:
        return await self.engine.generate_price_suggestion(book_id, condition)

    async def suggest_categories(self, title: str, description: str) -> list[str]:
        return await self.engine.suggest_categories(title, description)

    async def suggest_condition(
        self,
        title: str,
        description: str,
    ) -> ConditionSuggestionResponse:
        return _condition_suggestion(title, description)

    async def suggest_listing_description(
        self,
        title: str,
        condition: str,
        notes: str,
    ) -> ListingDescriptionSuggestionResponse:
        return _listing_description_suggestion(title, condition, notes)

    async def prioritize_fraud_review(
        self,
        title: str,
        description: str,
        price_amount_cents: int | None,
    ) -> FraudPriorityResponse:
        return _fraud_priority(title, description, price_amount_cents)

    async def get_similar_listings(self, listing_id: int, limit: int = 10) -> list[Listing]:
        return await self.engine.get_similar_listings(listing_id, limit)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_recommendation(self, public_id: str) -> Recommendation:
        rec = await self.repo.get_by_public_id(public_id)
        if rec is None:
            raise RecommendationNotFoundError()
        return rec


def _recommendation_response(rec: Recommendation) -> RecommendationResponse:
    return RecommendationResponse(
        confidence=rec.confidence,
        entity_id=rec.entity_id,
        entity_type=rec.entity_type,  # type: ignore[arg-type]
        id=rec.public_id,
        is_dismissed=rec.is_dismissed,
        model=rec.model,
        model_version=rec.model_version,
        provider=rec.provider,
        reason=rec.reason,
        score=rec.score,
        source=rec.source,  # type: ignore[arg-type]
    )


def _assistance_base(confidence: float) -> dict[str, Any]:
    return {
        "confidence": round(confidence, 2),
        "editable": True,
        "human_confirmation_required": True,
        "model": ASSISTANCE_MODEL,
        "model_version": ASSISTANCE_MODEL_VERSION,
        "provider": ASSISTANCE_PROVIDER,
    }


def _condition_suggestion(title: str, description: str) -> ConditionSuggestionResponse:
    combined = f"{title} {description}".lower()
    if any(token in combined for token in ("sealed", "unopened", "brand new")):
        condition = "new_sealed"
        confidence = 0.82
        explanation = "The text suggests the book is unopened or sealed."
    elif any(token in combined for token in ("like new", "unused", "no marks")):
        condition = "like_new"
        confidence = 0.76
        explanation = "The text suggests minimal handling and no visible marks."
    elif any(token in combined for token in ("excellent", "very good", "minor shelf")):
        condition = "very_good"
        confidence = 0.68
        explanation = "The text suggests light use with minor wear."
    elif any(token in combined for token in ("highlight", "notes", "worn", "used")):
        condition = "good"
        confidence = 0.62
        explanation = "The text mentions normal used-book wear or annotations."
    elif any(token in combined for token in ("missing", "water", "torn", "loose binding")):
        condition = "poor"
        confidence = 0.7
        explanation = "The text mentions damage that materially affects condition."
    else:
        condition = "good"
        confidence = 0.45
        explanation = "There is not enough detail, so the safest editable default is good."
    return ConditionSuggestionResponse(
        **_assistance_base(confidence),
        alternatives=["like_new", "very_good", "good", "acceptable", "poor"],
        explanation=explanation,
        suggested_condition=condition,
    )


def _listing_description_suggestion(
    title: str,
    condition: str,
    notes: str,
) -> ListingDescriptionSuggestionResponse:
    title_text = title.strip() or "Book"
    condition_text = condition.replace("_", " ").strip() or "used"
    note_text = notes.strip()
    sentences = [
        f"{title_text} in {condition_text} condition.",
        "Best suited for readers who want a usable copy and can review the photos before purchase.",
    ]
    if note_text:
        sentences.insert(1, note_text)
    return ListingDescriptionSuggestionResponse(
        **_assistance_base(0.58 if note_text else 0.42),
        suggested_description=" ".join(sentences),
        unsupported_metadata_warning=(
            "Only user-provided details were used; verify edition, author, ISBN, and included "
            "materials before publishing."
        ),
    )


def _fraud_priority(
    title: str,
    description: str,
    price_amount_cents: int | None,
) -> FraudPriorityResponse:
    combined = f"{title} {description}".lower()
    reasons: list[str] = []
    if any(token in combined for token in ("whatsapp", "telegram", "pay outside", "upi direct")):
        reasons.append("Asks users to move payment or conversation outside the platform.")
    if any(token in combined for token in ("pdf copy", "pirated", "counterfeit", "replica")):
        reasons.append("Mentions possible piracy or counterfeit material.")
    if any(token in combined for token in ("urgent", "today only", "no questions")):
        reasons.append("Uses high-pressure language common in risky listings.")
    if price_amount_cents is not None and price_amount_cents <= 100:
        reasons.append("Price is unusually low for a paid listing.")

    priority: ReviewPriority = "low"
    if len(reasons) >= 2:
        priority = "high"
    elif reasons:
        priority = "medium"
    confidence = min(0.9, 0.4 + 0.18 * len(reasons))
    return FraudPriorityResponse(
        **_assistance_base(confidence),
        auto_action_allowed=False,
        priority=priority,
        reasons=reasons,
        review_only=True,
    )


def _encode_cursor(offset: int) -> str:
    payload = json.dumps({"offset": offset}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(payload).decode()


def _decode_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except (ValueError, json.JSONDecodeError):
        return 0
    offset = payload.get("offset")
    if not isinstance(offset, int) or offset < 0:
        return 0
    return offset
