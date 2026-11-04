"""Create recommendations tables.

Revision ID: 0015_recommendations
Revises: 0014_professional_sellers
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_recommendations"
down_revision: str | None = "0014_professional_sellers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=26), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=24), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shown_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "entity_type in ('book', 'listing', 'seller', 'community', 'event', 'club')",
            name="entity_type",
        ),
        sa.CheckConstraint(
            "source in ('reading_history', 'wishlist', 'search_history', 'community',"
            " 'location', 'similar_users', 'genre', 'trending')",
            name="source",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_recommendations_user_entity_dismissed",
        "recommendations",
        ["user_id", "entity_type", "is_dismissed"],
    )
    op.create_index(
        "ix_recommendations_user_score",
        "recommendations",
        ["user_id", "score"],
    )
    op.create_index(
        "ix_recommendations_entity_type_entity_id",
        "recommendations",
        ["entity_type", "entity_id"],
    )
    op.create_index("ix_recommendations_public_id", "recommendations", ["public_id"], unique=True)

    op.create_table(
        "recommendation_feedbacks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=26), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("recommendation_id", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "feedback_type in ('helpful', 'not_helpful', 'not_interested', 'already_have')",
            name="feedback_type",
        ),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint(
            "user_id", "recommendation_id", name="uq_recommendation_feedbacks_pair"
        ),
    )
    op.create_index("ix_recommendation_feedbacks_user_id", "recommendation_feedbacks", ["user_id"])
    op.create_index(
        "ix_recommendation_feedbacks_recommendation_id",
        "recommendation_feedbacks",
        ["recommendation_id"],
    )
    op.create_index(
        "ix_recommendation_feedbacks_public_id",
        "recommendation_feedbacks",
        ["public_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("recommendation_feedbacks")
    op.drop_table("recommendations")
