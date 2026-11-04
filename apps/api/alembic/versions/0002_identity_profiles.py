"""Create identity and profile tables.

Revision ID: 0002_identity_profiles
Revises: 0001_foundation
Create Date: 2026-06-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_identity_profiles"
down_revision: str | None = "0001_foundation"
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


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mobile_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('active', 'pending_deletion', 'deleted', 'suspended')",
            name="status",
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("public_id", name="uq_users_public_id"),
    )
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("username", sa.String(length=40), nullable=True),
        sa.Column("profile_image_url", sa.String(length=1000), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("approximate_location", sa.String(length=160), nullable=True),
        sa.Column("institution", sa.String(length=160), nullable=True),
        sa.Column("course_department", sa.String(length=160), nullable=True),
        sa.Column("privacy_level", sa.String(length=24), nullable=False, server_default="public"),
        sa.Column("hide_location", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hide_institution", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hide_followers", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hide_shelves", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "allow_messages_from", sa.String(length=24), nullable=False, server_default="everyone"
        ),
        sa.Column("show_online_status", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("show_read_receipts", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "languages",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "favorite_genres",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "favorite_authors",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "favorite_books",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "reading_interests",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "privacy_level in ('public', 'members_only', 'private')",
            name="privacy_level",
        ),
        sa.CheckConstraint(
            "allow_messages_from in ('everyone', 'members', 'none')",
            name="allow_messages_from",
        ),
        sa.UniqueConstraint("public_id", name="uq_user_profiles_public_id"),
        sa.UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
        sa.UniqueConstraint("username", name="uq_user_profiles_username"),
    )

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("locale", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("timezone", sa.String(length=80), nullable=False, server_default="UTC"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_user_preferences_public_id"),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )

    op.create_table(
        "user_devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("device_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("device_name", sa.String(length=120), nullable=True),
        sa.Column("device_type", sa.String(length=40), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_from_user_agent", sa.String(length=512), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_user_devices_public_id"),
        sa.UniqueConstraint("user_id", "device_fingerprint", name="uq_user_devices_fingerprint"),
    )
    op.create_index("ix_user_devices_user_id", "user_devices", ["user_id"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "device_id",
            sa.Integer(),
            sa.ForeignKey("user_devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("refresh_token_hash", sa.String(length=128), nullable=False),
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=80), nullable=True),
        sa.Column("reuse_detected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_user_sessions_public_id"),
        sa.UniqueConstraint("refresh_token_hash", name="uq_user_sessions_refresh_token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])

    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_account_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
        sa.CheckConstraint("provider in ('google', 'apple')", name="provider"),
        sa.UniqueConstraint("public_id", name="uq_social_accounts_public_id"),
        sa.UniqueConstraint(
            "provider", "provider_account_id", name="uq_social_accounts_provider_account"
        ),
        sa.UniqueConstraint("user_id", "provider", name="uq_social_accounts_user_provider"),
    )

    op.create_table(
        "user_verifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("verification_type", sa.String(length=40), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("destination", sa.String(length=320), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "verification_type in "
            "('email', 'mobile', 'password_reset', 'data_export', 'account_deletion')",
            name="verification_type",
        ),
        sa.UniqueConstraint("public_id", name="uq_user_verifications_public_id"),
        sa.UniqueConstraint("token_hash", name="uq_user_verifications_token_hash"),
    )
    op.create_index(
        "ix_user_verifications_user_type",
        "user_verifications",
        ["user_id", "verification_type"],
    )

    op.create_table(
        "user_blocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "blocker_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "blocked_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=280), nullable=True),
        *timestamps(),
        sa.CheckConstraint("blocker_user_id <> blocked_user_id", name="not_self"),
        sa.UniqueConstraint("public_id", name="uq_user_blocks_public_id"),
        sa.UniqueConstraint("blocker_user_id", "blocked_user_id", name="uq_user_blocks_pair"),
    )
    op.create_index("ix_user_blocks_blocked_user_id", "user_blocks", ["blocked_user_id"])

    op.create_table(
        "consent_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("terms_version", sa.String(length=40), nullable=False),
        sa.Column("privacy_version", sa.String(length=40), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_consent_records_public_id"),
    )
    op.create_index("ix_consent_records_user_id", "consent_records", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column(
            "context_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_audit_logs_public_id"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_target_user_id", "audit_logs", ["target_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_target_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_consent_records_user_id", table_name="consent_records")
    op.drop_table("consent_records")
    op.drop_index("ix_user_blocks_blocked_user_id", table_name="user_blocks")
    op.drop_table("user_blocks")
    op.drop_index("ix_user_verifications_user_type", table_name="user_verifications")
    op.drop_table("user_verifications")
    op.drop_table("social_accounts")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_user_devices_user_id", table_name="user_devices")
    op.drop_table("user_devices")
    op.drop_table("user_preferences")
    op.drop_table("user_profiles")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_table("users")
