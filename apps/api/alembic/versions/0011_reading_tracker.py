"""Create reading tracker tables.

Revision ID: 0011_reading_tracker
Revises: 0010_clubs_events
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_reading_tracker"
down_revision: str | None = "0010_clubs_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    ]


def public_id_column() -> sa.Column:
    return sa.Column("public_id", sa.String(length=26), nullable=False)


def jsonb_object() -> sa.ColumnElement:
    return sa.text("'{}'::jsonb")


def upgrade() -> None:
    op.create_table(
        "shelves",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("shelf_type", sa.String(length=40), nullable=False, server_default="custom"),
        sa.Column("visibility", sa.String(length=24), nullable=False, server_default="private"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.CheckConstraint(
            "shelf_type in ("
            "'want_to_read', 'currently_reading', 'finished', 'did_not_finish', 'owned', "
            "'previously_owned', 'available_for_exchange', 'available_for_lending', "
            "'favorites', 'academic_books', 'rare_collection', 'custom')",
            name="shelf_type",
        ),
        sa.CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        sa.UniqueConstraint("public_id", name="uq_shelves_public_id"),
        sa.UniqueConstraint("user_id", "slug", name="uq_shelves_user_slug"),
    )
    op.create_index("ix_shelves_user_id", "shelves", ["user_id"])
    op.create_index("ix_shelves_visibility", "shelves", ["visibility"])

    op.create_table(
        "shelf_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "shelf_id",
            sa.Integer(),
            sa.ForeignKey("shelves.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_shelf_items_public_id"),
        sa.UniqueConstraint("shelf_id", "book_edition_id", name="uq_shelf_items_book"),
    )
    op.create_index("ix_shelf_items_user_id", "shelf_items", ["user_id"])
    op.create_index("ix_shelf_items_book_edition_id", "shelf_items", ["book_edition_id"])

    op.create_table(
        "reading_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="want_to_read"),
        sa.Column("current_page", sa.Integer(), nullable=True),
        sa.Column("percent_complete", sa.Integer(), nullable=True),
        sa.Column("started_on", sa.Date(), nullable=True),
        sa.Column("finished_on", sa.Date(), nullable=True),
        sa.Column("last_progress_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_reading_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "daily_minutes_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("reread_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('want_to_read', 'currently_reading', 'finished', 'did_not_finish')",
            name="status",
        ),
        sa.CheckConstraint("current_page is null or current_page >= 0", name="current_page"),
        sa.CheckConstraint(
            "percent_complete is null or (percent_complete >= 0 and percent_complete <= 100)",
            name="percent_complete",
        ),
        sa.CheckConstraint("rating is null or (rating >= 1 and rating <= 5)", name="rating"),
        sa.CheckConstraint("reread_count >= 0", name="reread_count_non_negative"),
        sa.CheckConstraint(
            "total_reading_minutes >= 0",
            name="total_reading_minutes_non_negative",
        ),
        sa.UniqueConstraint("public_id", name="uq_reading_progress_public_id"),
        sa.UniqueConstraint(
            "user_id",
            "book_edition_id",
            name="uq_reading_progress_user_book",
        ),
    )
    op.create_index(
        "ix_reading_progress_user_status",
        "reading_progress",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_reading_progress_book_edition_id",
        "reading_progress",
        ["book_edition_id"],
    )

    op.create_table(
        "reading_notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "progress_id",
            sa.Integer(),
            sa.ForeignKey("reading_progress.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note_type", sa.String(length=24), nullable=False, server_default="note"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("percent_complete", sa.Integer(), nullable=True),
        sa.Column("visibility", sa.String(length=24), nullable=False, server_default="private"),
        sa.Column("client_note_id", sa.String(length=120), nullable=True),
        *timestamps(),
        sa.CheckConstraint("note_type in ('note', 'highlight', 'quote')", name="note_type"),
        sa.CheckConstraint("visibility in ('private', 'public')", name="visibility"),
        sa.CheckConstraint("page_number is null or page_number >= 0", name="page_number"),
        sa.CheckConstraint(
            "percent_complete is null or (percent_complete >= 0 and percent_complete <= 100)",
            name="percent_complete",
        ),
        sa.UniqueConstraint("public_id", name="uq_reading_notes_public_id"),
        sa.UniqueConstraint("user_id", "client_note_id", name="uq_reading_notes_client_note"),
    )
    op.create_index("ix_reading_notes_user_book", "reading_notes", ["user_id", "book_edition_id"])
    op.create_index("ix_reading_notes_visibility", "reading_notes", ["visibility"])

    op.create_table(
        "reading_goals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("goal_type", sa.String(length=40), nullable=False),
        sa.Column("scope", sa.String(length=24), nullable=False, server_default="personal"),
        sa.Column("target_value", sa.Integer(), nullable=False),
        sa.Column("current_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column(
            "target_metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "goal_type in ('books_per_year', 'pages_per_month', 'minutes_per_day', "
            "'genre', 'author', 'language', 'community_challenge', 'institution_challenge')",
            name="goal_type",
        ),
        sa.CheckConstraint("scope in ('personal', 'community', 'institution')", name="scope"),
        sa.CheckConstraint("status in ('active', 'completed', 'cancelled')", name="status"),
        sa.CheckConstraint("target_value > 0", name="target_value_positive"),
        sa.CheckConstraint("current_value >= 0", name="current_value_non_negative"),
        sa.UniqueConstraint("public_id", name="uq_reading_goals_public_id"),
    )
    op.create_index("ix_reading_goals_user_status", "reading_goals", ["user_id", "status"])
    op.create_index("ix_reading_goals_community_id", "reading_goals", ["community_id"])

    op.create_table(
        "reading_statistics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_type", sa.String(length=24), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("books_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_read", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minutes_read", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reading_streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "genres_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column(
            "authors_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column(
            "monthly_progress_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column(
            "year_summary_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
        sa.CheckConstraint("period_type in ('month', 'year', 'all_time')", name="period_type"),
        sa.CheckConstraint("books_completed >= 0", name="books_completed_non_negative"),
        sa.CheckConstraint("pages_read >= 0", name="pages_read_non_negative"),
        sa.CheckConstraint("minutes_read >= 0", name="minutes_read_non_negative"),
        sa.CheckConstraint(
            "reading_streak_days >= 0",
            name="reading_streak_days_non_negative",
        ),
        sa.UniqueConstraint("public_id", name="uq_reading_statistics_public_id"),
        sa.UniqueConstraint(
            "user_id",
            "period_type",
            "period_start",
            "timezone",
            name="uq_reading_statistics_period",
        ),
    )
    op.create_index(
        "ix_reading_statistics_user_period",
        "reading_statistics",
        ["user_id", "period_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_reading_statistics_user_period", table_name="reading_statistics")
    op.drop_table("reading_statistics")

    op.drop_index("ix_reading_goals_community_id", table_name="reading_goals")
    op.drop_index("ix_reading_goals_user_status", table_name="reading_goals")
    op.drop_table("reading_goals")

    op.drop_index("ix_reading_notes_visibility", table_name="reading_notes")
    op.drop_index("ix_reading_notes_user_book", table_name="reading_notes")
    op.drop_table("reading_notes")

    op.drop_index("ix_reading_progress_book_edition_id", table_name="reading_progress")
    op.drop_index("ix_reading_progress_user_status", table_name="reading_progress")
    op.drop_table("reading_progress")

    op.drop_index("ix_shelf_items_book_edition_id", table_name="shelf_items")
    op.drop_index("ix_shelf_items_user_id", table_name="shelf_items")
    op.drop_table("shelf_items")

    op.drop_index("ix_shelves_visibility", table_name="shelves")
    op.drop_index("ix_shelves_user_id", table_name="shelves")
    op.drop_table("shelves")
