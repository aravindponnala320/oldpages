from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.recommendations.models import Recommendation, RecommendationFeedback


class RecommendationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, rec_id: int) -> Recommendation | None:
        result = await self.session.execute(
            select(Recommendation).where(Recommendation.id == rec_id)
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: str) -> Recommendation | None:
        result = await self.session.execute(
            select(Recommendation).where(Recommendation.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: int,
        entity_type: str | None = None,
        source: str | None = None,
        limit: int = 20,
        cursor: int = 0,
    ) -> list[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.user_id == user_id,
                Recommendation.is_dismissed.is_(False),
            )
            .order_by(Recommendation.score.desc(), Recommendation.id.desc())
            .offset(cursor)
            .limit(limit)
        )
        if entity_type is not None:
            stmt = stmt.where(Recommendation.entity_type == entity_type)
        if source is not None:
            stmt = stmt.where(Recommendation.source == source)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_feedback(
        self,
        user_id: int,
        recommendation_id: int,
    ) -> RecommendationFeedback | None:
        result = await self.session.execute(
            select(RecommendationFeedback).where(
                RecommendationFeedback.user_id == user_id,
                RecommendationFeedback.recommendation_id == recommendation_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_recommendation(
        self,
        user_id: int,
        entity_type: str,
        entity_id: int,
        score: float,
        reason: str,
        source: str,
        confidence: float | None = None,
        model: str = "oldpages-rule-engine",
        model_version: str = "1",
        provider: str = "rules",
    ) -> Recommendation:
        result = await self.session.execute(
            select(Recommendation).where(
                Recommendation.user_id == user_id,
                Recommendation.entity_type == entity_type,
                Recommendation.entity_id == entity_id,
                Recommendation.source == source,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.confidence = score if confidence is None else confidence
            existing.model = model
            existing.model_version = model_version
            existing.provider = provider
            existing.score = score
            existing.reason = reason
            existing.is_dismissed = False
            existing.dismissed_at = None
            return existing
        rec = Recommendation(
            entity_id=entity_id,
            entity_type=entity_type,
            confidence=score if confidence is None else confidence,
            model=model,
            model_version=model_version,
            provider=provider,
            reason=reason,
            score=score,
            source=source,
            user_id=user_id,
        )
        self.session.add(rec)
        await self.session.flush()
        return rec

    async def mark_shown(self, recommendation_id: int) -> None:
        await self.session.execute(
            update(Recommendation)
            .where(
                Recommendation.id == recommendation_id,
                Recommendation.shown_at.is_(None),
            )
            .values(shown_at=datetime.now(UTC))
        )

    async def mark_clicked(self, recommendation_id: int) -> None:
        await self.session.execute(
            update(Recommendation)
            .where(Recommendation.id == recommendation_id)
            .values(clicked_at=datetime.now(UTC))
        )

    async def delete_old_dismissed(self, cutoff: datetime) -> None:
        await self.session.execute(
            delete(Recommendation).where(
                Recommendation.is_dismissed.is_(True),
                Recommendation.dismissed_at <= cutoff,
            )
        )

    async def delete_old_recommendations(self, cutoff: datetime) -> None:
        await self.session.execute(
            delete(Recommendation).where(
                Recommendation.created_at <= cutoff,
                Recommendation.is_dismissed.is_(False),
                Recommendation.clicked_at.is_(None),
            )
        )

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()
