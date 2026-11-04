"""Create community tables.

Revision ID: 0009_communities
Revises: 0008_trust_moderation
Create Date: 2026-06-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_communities"
down_revision: str | None = "0008_trust_moderation"
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
        "communities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "owner_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=1000), nullable=True),
        sa.Column("community_type", sa.String(length=40), nullable=False, server_default="general"),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="public"),
        sa.Column(
            "membership_policy",
            sa.String(length=32),
            nullable=False,
            server_default="open",
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("institution", sa.String(length=180), nullable=True),
        sa.Column("genre", sa.String(length=120), nullable=True),
        sa.Column("language", sa.String(length=40), nullable=True),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "settings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "visibility in ('public', 'private', 'secret', 'institution_verified')",
            name="visibility",
        ),
        sa.CheckConstraint(
            "membership_policy in ('open', 'request', 'approval', 'institution_verified')",
            name="membership_policy",
        ),
        sa.CheckConstraint(
            "community_type in ("
            "'college', 'university', 'school', 'area', 'city', 'apartment', 'workplace', "
            "'language', 'genre', 'author', 'series', 'book', 'exam', 'course', 'profession', "
            "'age_group', 'reading_goal', 'library', 'bookstore', 'publisher', 'social_cause', "
            "'local', 'general')",
            name="community_type",
        ),
        sa.CheckConstraint("status in ('active', 'archived', 'suspended')", name="status"),
        sa.UniqueConstraint("public_id", name="uq_communities_public_id"),
        sa.UniqueConstraint("slug", name="uq_communities_slug"),
    )
    op.create_index("ix_communities_visibility_status", "communities", ["visibility", "status"])
    op.create_index("ix_communities_city_country", "communities", ["city", "country"])
    op.create_index("ix_communities_institution", "communities", ["institution"])
    op.create_index("ix_communities_genre", "communities", ["genre"])
    op.create_index("ix_communities_book_edition_id", "communities", ["book_edition_id"])

    op.create_table(
        "community_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column(
            "permissions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_community_roles_public_id"),
        sa.UniqueConstraint("community_id", "name", name="uq_community_roles_name"),
    )
    op.create_index("ix_community_roles_community_id", "community_roles", ["community_id"])

    op.create_table(
        "community_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("community_roles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column(
            "answers_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("muted_until", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('pending', 'active', 'rejected', 'banned', 'muted')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_community_members_public_id"),
        sa.UniqueConstraint("community_id", "user_id", name="uq_community_members_user"),
    )
    op.create_index("ix_community_members_user_status", "community_members", ["user_id", "status"])
    op.create_index(
        "ix_community_members_community_status",
        "community_members",
        ["community_id", "status"],
    )

    op.create_table(
        "community_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_community_rules_public_id"),
    )
    op.create_index("ix_community_rules_community_id", "community_rules", ["community_id"])

    op.create_table(
        "community_channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("channel_type", sa.String(length=32), nullable=False, server_default="general"),
        sa.Column("visibility", sa.String(length=24), nullable=False, server_default="members"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.CheckConstraint(
            "channel_type in ('general', 'announcements', 'marketplace', 'questions', 'resources')",
            name="channel_type",
        ),
        sa.CheckConstraint("visibility in ('public', 'members', 'moderators')", name="visibility"),
        sa.UniqueConstraint("public_id", name="uq_community_channels_public_id"),
        sa.UniqueConstraint("community_id", "slug", name="uq_community_channels_slug"),
    )
    op.create_index("ix_community_channels_community_id", "community_channels", ["community_id"])

    op.create_table(
        "community_posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel_id",
            sa.Integer(),
            sa.ForeignKey("community_channels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "author_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("post_type", sa.String(length=40), nullable=False, server_default="text"),
        sa.Column("title", sa.String(length=240), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "poll_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="published"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_announcement", sa.Boolean(), nullable=False, server_default=sa.false()),
        *timestamps(),
        sa.CheckConstraint(
            "post_type in ("
            "'text', 'review', 'photo', 'video', 'poll', 'question', 'recommendation', 'quote', "
            "'reading_update', 'listing', 'exchange_request', 'donation_request', 'event', "
            "'challenge', 'resource', 'announcement')",
            name="post_type",
        ),
        sa.CheckConstraint(
            "status in ('published', 'pending_review', 'hidden', 'deleted')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_community_posts_public_id"),
    )
    op.create_index(
        "ix_community_posts_feed",
        "community_posts",
        ["community_id", "status", "is_pinned", "created_at"],
    )
    op.create_index("ix_community_posts_author_user_id", "community_posts", ["author_user_id"])

    op.create_table(
        "post_comments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "post_id",
            sa.Integer(),
            sa.ForeignKey("community_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_comment_id",
            sa.Integer(),
            sa.ForeignKey("post_comments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="published"),
        *timestamps(),
        sa.CheckConstraint("status in ('published', 'hidden', 'deleted')", name="status"),
        sa.UniqueConstraint("public_id", name="uq_post_comments_public_id"),
    )
    op.create_index("ix_post_comments_post_created", "post_comments", ["post_id", "created_at"])
    op.create_index("ix_post_comments_author_user_id", "post_comments", ["author_user_id"])

    op.create_table(
        "post_reactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "post_id",
            sa.Integer(),
            sa.ForeignKey("community_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reaction_type", sa.String(length=24), nullable=False, server_default="like"),
        *timestamps(),
        sa.CheckConstraint(
            "reaction_type in ('like', 'love', 'insightful', 'upvote', 'celebrate')",
            name="reaction_type",
        ),
        sa.UniqueConstraint("public_id", name="uq_post_reactions_public_id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_reactions_user"),
    )
    op.create_index("ix_post_reactions_post_id", "post_reactions", ["post_id"])

    op.create_table(
        "community_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "community_id",
            sa.Integer(),
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reporter_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_type", sa.String(length=24), nullable=False),
        sa.Column(
            "target_community_post_id",
            sa.Integer(),
            sa.ForeignKey("community_posts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_post_comment_id",
            sa.Integer(),
            sa.ForeignKey("post_comments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_member_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.String(length=80), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="open"),
        *timestamps(),
        sa.CheckConstraint(
            "target_type in ('community', 'post', 'comment', 'member')",
            name="target_type",
        ),
        sa.CheckConstraint("status in ('open', 'resolved', 'dismissed')", name="status"),
        sa.UniqueConstraint("public_id", name="uq_community_reports_public_id"),
    )
    op.create_index(
        "ix_community_reports_community_status",
        "community_reports",
        ["community_id", "status"],
    )
    op.create_index(
        "ix_community_reports_reporter_user_id",
        "community_reports",
        ["reporter_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_community_reports_reporter_user_id", table_name="community_reports")
    op.drop_index("ix_community_reports_community_status", table_name="community_reports")
    op.drop_table("community_reports")

    op.drop_index("ix_post_reactions_post_id", table_name="post_reactions")
    op.drop_table("post_reactions")

    op.drop_index("ix_post_comments_author_user_id", table_name="post_comments")
    op.drop_index("ix_post_comments_post_created", table_name="post_comments")
    op.drop_table("post_comments")

    op.drop_index("ix_community_posts_author_user_id", table_name="community_posts")
    op.drop_index("ix_community_posts_feed", table_name="community_posts")
    op.drop_table("community_posts")

    op.drop_index("ix_community_channels_community_id", table_name="community_channels")
    op.drop_table("community_channels")

    op.drop_index("ix_community_rules_community_id", table_name="community_rules")
    op.drop_table("community_rules")

    op.drop_index("ix_community_members_community_status", table_name="community_members")
    op.drop_index("ix_community_members_user_status", table_name="community_members")
    op.drop_table("community_members")

    op.drop_index("ix_community_roles_community_id", table_name="community_roles")
    op.drop_table("community_roles")

    op.drop_index("ix_communities_book_edition_id", table_name="communities")
    op.drop_index("ix_communities_genre", table_name="communities")
    op.drop_index("ix_communities_institution", table_name="communities")
    op.drop_index("ix_communities_city_country", table_name="communities")
    op.drop_index("ix_communities_visibility_status", table_name="communities")
    op.drop_table("communities")
