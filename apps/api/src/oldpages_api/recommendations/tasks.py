from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.models import User
from oldpages_api.recommendations.engine import RecommendationEngine
from oldpages_api.recommendations.models import Recommendation
from oldpages_api.recommendations.repository import RecommendationRepository

logger = logging.getLogger(__name__)


async def generate_recommendations_for_user(user_id: int, session: AsyncSession) -> None:
    """Generate and persist recommendations for a single user."""
    engine = RecommendationEngine(session)
    repo = RecommendationRepository(session)
    try:
        recs = await engine.generate_for_user(user_id)
        for item in recs:
            await repo.upsert_recommendation(
                user_id=user_id,
                entity_type=item["entity_type"],
                entity_id=item["entity_id"],
                score=item["score"],
                reason=item["reason"],
                source=item["source"],
            )
        await repo.commit()
        logger.info("Generated %d recommendations for user %d", len(recs), user_id)
    except Exception:
        logger.exception("Error generating recommendations for user %d", user_id)
        raise


async def generate_recommendations_batch(session: AsyncSession) -> None:
    """Run recommendation generation for all active users."""
    result = await session.execute(select(User.id).where(User.status == "active").order_by(User.id))
    user_ids = [row[0] for row in result.all()]
    logger.info("Starting batch recommendation generation for %d users", len(user_ids))
    for user_id in user_ids:
        try:
            await generate_recommendations_for_user(user_id, session)
        except Exception:
            logger.exception("Skipping user %d due to error", user_id)
            continue
    logger.info("Batch recommendation generation complete")


async def cleanup_old_recommendations(session: AsyncSession) -> None:
    """Delete dismissed/old recommendations older than 30 days."""
    cutoff = datetime.now(UTC) - timedelta(days=30)
    result = await session.execute(
        delete(Recommendation).where(
            (Recommendation.is_dismissed.is_(True) & (Recommendation.dismissed_at <= cutoff))
            | (
                Recommendation.is_dismissed.is_(False)
                & (Recommendation.created_at <= cutoff)
                & Recommendation.clicked_at.is_(None)
            )
        )
    )
    deleted = int(getattr(result, "rowcount", 0) or 0)
    await session.commit()
    logger.info("Cleaned up %d old recommendations", deleted)
