"""Create club, readalong, buddy read, and event tables.

Revision ID: 0010_clubs_events
Revises: 0009_communities
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_clubs_events"
down_revision: str | None = "0009_communities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def public_id_column() -> sa.Column:
    return sa.Column("public_id", sa.String(length=26), nullable=False)


def jsonb_object() -> sa.ColumnElement:
    return sa.text("'{}'::jsonb")


def jsonb_array() -> sa.ColumnElement:
    return sa.text("'[]'::jsonb")


def upgrade() -> None:
    op.create_table(
        "book_clubs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "owner_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=24), nullable=False, server_default="public"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("timezone", sa.String(length=80), nullable=False, server_default="UTC"),
        sa.Column(
            "settings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        sa.CheckConstraint(
            "status in ('active', 'archived', 'suspended')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_book_clubs_public_id"),
        sa.UniqueConstraint("slug", name="uq_book_clubs_slug"),
    )
    op.create_index("ix_book_clubs_owner_user_id", "book_clubs", ["owner_user_id"])
    op.create_index("ix_book_clubs_community_id", "book_clubs", ["community_id"])
    op.create_index("ix_book_clubs_visibility_status", "book_clubs", ["visibility", "status"])

    op.create_table(
        "club_books",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "club_id",
            sa.Integer(),
            sa.ForeignKey("book_clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="next"),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discussion_guide", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("status in ('current', 'next', 'past')", name="status"),
        sa.UniqueConstraint("public_id", name="uq_club_books_public_id"),
    )
    op.create_index("ix_club_books_club_status", "club_books", ["club_id", "status"])
    op.create_index("ix_club_books_book_edition_id", "club_books", ["book_edition_id"])

    op.create_table(
        "book_nominations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "club_id",
            sa.Integer(),
            sa.ForeignKey("book_clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "nominator_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cycle_key", sa.String(length=80), nullable=False, server_default="default"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        *timestamps(),
        sa.CheckConstraint("status in ('active', 'selected', 'withdrawn')", name="status"),
        sa.UniqueConstraint("public_id", name="uq_book_nominations_public_id"),
        sa.UniqueConstraint(
            "club_id",
            "cycle_key",
            "book_edition_id",
            name="uq_book_nominations_cycle_book",
        ),
    )
    op.create_index(
        "ix_book_nominations_club_cycle",
        "book_nominations",
        ["club_id", "cycle_key", "status"],
    )

    op.create_table(
        "book_votes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "club_id",
            sa.Integer(),
            sa.ForeignKey("book_clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "nomination_id",
            sa.Integer(),
            sa.ForeignKey("book_nominations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "voter_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cycle_key", sa.String(length=80), nullable=False, server_default="default"),
        sa.Column("rank", sa.Integer(), nullable=False),
        *timestamps(),
        sa.CheckConstraint("rank > 0", name="rank_positive"),
        sa.UniqueConstraint("public_id", name="uq_book_votes_public_id"),
        sa.UniqueConstraint(
            "nomination_id",
            "voter_user_id",
            name="uq_book_votes_nomination_voter",
        ),
        sa.UniqueConstraint(
            "club_id",
            "cycle_key",
            "voter_user_id",
            "rank",
            name="uq_book_votes_voter_rank",
        ),
    )
    op.create_index("ix_book_votes_club_cycle", "book_votes", ["club_id", "cycle_key"])

    op.create_table(
        "reading_milestones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "club_book_id",
            sa.Integer(),
            sa.ForeignKey("club_books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("position_type", sa.String(length=24), nullable=False),
        sa.Column("position_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discussion_prompt", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "position_type in ('chapter', 'page', 'percent', 'whole_book')",
            name="position_type",
        ),
        sa.CheckConstraint("position_value >= 0", name="position_value_non_negative"),
        sa.UniqueConstraint("public_id", name="uq_reading_milestones_public_id"),
    )
    op.create_index(
        "ix_reading_milestones_club_book_id",
        "reading_milestones",
        ["club_book_id"],
    )

    op.create_table(
        "buddy_reads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "creator_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("visibility", sa.String(length=24), nullable=False, server_default="private"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_participants", sa.Integer(), nullable=False, server_default="4"),
        sa.Column(
            "participant_user_ids_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        sa.Column(
            "progress_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        sa.CheckConstraint(
            "status in ('active', 'completed', 'cancelled')",
            name="status",
        ),
        sa.CheckConstraint("max_participants > 0", name="max_participants_positive"),
        sa.UniqueConstraint("public_id", name="uq_buddy_reads_public_id"),
    )
    op.create_index("ix_buddy_reads_book_edition_id", "buddy_reads", ["book_edition_id"])
    op.create_index("ix_buddy_reads_creator_user_id", "buddy_reads", ["creator_user_id"])

    op.create_table(
        "readalongs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "host_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=24), nullable=False, server_default="public"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="scheduled"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=False, server_default="UTC"),
        sa.Column(
            "chapter_schedule_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        sa.Column(
            "moderator_user_ids_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        *timestamps(),
        sa.CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        sa.CheckConstraint(
            "status in ('scheduled', 'active', 'completed', 'cancelled')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_readalongs_public_id"),
    )
    op.create_index("ix_readalongs_book_edition_id", "readalongs", ["book_edition_id"])
    op.create_index("ix_readalongs_community_id", "readalongs", ["community_id"])
    op.create_index("ix_readalongs_host_user_id", "readalongs", ["host_user_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "organizer_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "club_id",
            sa.Integer(),
            sa.ForeignKey("book_clubs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("visibility", sa.String(length=24), nullable=False, server_default="public"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="scheduled"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("location_name", sa.String(length=180), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("online_url", sa.String(length=1000), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("checkin_code", sa.String(length=32), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "event_type in ("
            "'book_club_meeting', 'book_exchange', 'used_book_fair', 'donation_drive', "
            "'author_meetup', 'signing', 'reading_session', 'silent_reading', "
            "'childrens_story_session', 'library_event', 'college_textbook_sale', "
            "'writing_workshop', 'poetry_reading', 'online_discussion', 'author_interview')",
            name="event_type",
        ),
        sa.CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        sa.CheckConstraint("status in ('scheduled', 'cancelled', 'completed')", name="status"),
        sa.CheckConstraint("capacity is null or capacity > 0", name="capacity_positive"),
        sa.UniqueConstraint("public_id", name="uq_events_public_id"),
        sa.UniqueConstraint("checkin_code", name="uq_events_checkin_code"),
    )
    op.create_index("ix_events_starts_at", "events", ["starts_at"])
    op.create_index("ix_events_community_id", "events", ["community_id"])
    op.create_index("ix_events_club_id", "events", ["club_id"])
    op.create_index("ix_events_organizer_user_id", "events", ["organizer_user_id"])

    op.create_table(
        "event_rsvps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="going"),
        sa.Column("guest_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(length=500), nullable=True),
        *timestamps(),
        sa.CheckConstraint("status in ('going', 'cancelled', 'waitlisted')", name="status"),
        sa.CheckConstraint("guest_count >= 0", name="guest_count_non_negative"),
        sa.UniqueConstraint("public_id", name="uq_event_rsvps_public_id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_rsvps_user"),
    )
    op.create_index(
        "ix_event_rsvps_event_status",
        "event_rsvps",
        ["event_id", "status"],
    )

    op.create_table(
        "event_waitlists",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="waiting"),
        sa.Column("guest_count", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.CheckConstraint("status in ('waiting', 'promoted', 'cancelled')", name="status"),
        sa.CheckConstraint("position > 0", name="position_positive"),
        sa.CheckConstraint("guest_count >= 0", name="guest_count_non_negative"),
        sa.UniqueConstraint("public_id", name="uq_event_waitlists_public_id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_waitlists_user"),
    )
    op.create_index(
        "ix_event_waitlists_event_status_position",
        "event_waitlists",
        ["event_id", "status", "position"],
    )

    op.create_table(
        "event_checkins",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "checked_in_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checkin_code", sa.String(length=32), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_event_checkins_public_id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_checkins_user"),
    )
    op.create_index("ix_event_checkins_event_id", "event_checkins", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_event_checkins_event_id", table_name="event_checkins")
    op.drop_table("event_checkins")

    op.drop_index("ix_event_waitlists_event_status_position", table_name="event_waitlists")
    op.drop_table("event_waitlists")

    op.drop_index("ix_event_rsvps_event_status", table_name="event_rsvps")
    op.drop_table("event_rsvps")

    op.drop_index("ix_events_organizer_user_id", table_name="events")
    op.drop_index("ix_events_club_id", table_name="events")
    op.drop_index("ix_events_community_id", table_name="events")
    op.drop_index("ix_events_starts_at", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_readalongs_host_user_id", table_name="readalongs")
    op.drop_index("ix_readalongs_community_id", table_name="readalongs")
    op.drop_index("ix_readalongs_book_edition_id", table_name="readalongs")
    op.drop_table("readalongs")

    op.drop_index("ix_buddy_reads_creator_user_id", table_name="buddy_reads")
    op.drop_index("ix_buddy_reads_book_edition_id", table_name="buddy_reads")
    op.drop_table("buddy_reads")

    op.drop_index("ix_reading_milestones_club_book_id", table_name="reading_milestones")
    op.drop_table("reading_milestones")

    op.drop_index("ix_book_votes_club_cycle", table_name="book_votes")
    op.drop_table("book_votes")

    op.drop_index("ix_book_nominations_club_cycle", table_name="book_nominations")
    op.drop_table("book_nominations")

    op.drop_index("ix_club_books_book_edition_id", table_name="club_books")
    op.drop_index("ix_club_books_club_status", table_name="club_books")
    op.drop_table("club_books")

    op.drop_index("ix_book_clubs_visibility_status", table_name="book_clubs")
    op.drop_index("ix_book_clubs_community_id", table_name="book_clubs")
    op.drop_index("ix_book_clubs_owner_user_id", table_name="book_clubs")
    op.drop_table("book_clubs")
