from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oldpages_api.identity.models import User
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Recommendation(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint(
            "entity_type in ('book', 'listing', 'seller', 'community', 'event', 'club')",
            name="entity_type",
        ),
        CheckConstraint(
            "source in ('reading_history', 'wishlist', 'search_history', 'community',"
            " 'location', 'similar_users', 'genre', 'trending')",
            name="source",
        ),
        Index("ix_recommendations_user_entity_dismissed", "user_id", "entity_type", "is_dismissed"),
        Index("ix_recommendations_user_score", "user_id", "score"),
        Index("ix_recommendations_entity_type_entity_id", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    entity_type: Mapped[str] = mapped_column(String(24), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="rules")
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="oldpages-rule-engine")
    model_version: Mapped[str] = mapped_column(String(40), nullable=False, default="1")
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    feedbacks: Mapped[list[RecommendationFeedback]] = relationship(
        back_populates="recommendation",
        cascade="all, delete-orphan",
    )
    user: Mapped[User] = relationship()


class RecommendationFeedback(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "recommendation_feedbacks"
    __table_args__ = (
        CheckConstraint(
            "feedback_type in ('helpful', 'not_helpful', 'not_interested', 'already_have')",
            name="feedback_type",
        ),
        UniqueConstraint("user_id", "recommendation_id", name="uq_recommendation_feedbacks_pair"),
        Index("ix_recommendation_feedbacks_user_id", "user_id"),
        Index("ix_recommendation_feedbacks_recommendation_id", "recommendation_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE")
    )
    feedback_type: Mapped[str] = mapped_column(String(24), nullable=False)

    recommendation: Mapped[Recommendation] = relationship(back_populates="feedbacks")
    user: Mapped[User] = relationship()


__all__ = [
    "Recommendation",
    "RecommendationFeedback",
]
