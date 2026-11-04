"""Create trust and moderation tables.

Revision ID: 0008_trust_moderation
Revises: 0007_commerce
Create Date: 2026-06-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_trust_moderation"
down_revision: str | None = "0007_commerce"
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
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "reporter_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_type", sa.String(length=24), nullable=False),
        sa.Column("reason", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="open"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "evidence_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column(
            "target_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_message_id",
            sa.Integer(),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_review_id",
            sa.Integer(),
            sa.ForeignKey("reviews.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *timestamps(),
        sa.CheckConstraint(
            "target_type in ('user', 'listing', 'message', 'review', 'copyright')",
            name="target_type",
        ),
        sa.CheckConstraint(
            "severity in ('low', 'medium', 'high', 'critical')",
            name="severity",
        ),
        sa.CheckConstraint(
            "status in ('open', 'in_review', 'resolved', 'dismissed', 'appealed')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_reports_public_id"),
    )
    op.create_index("ix_reports_reporter_user_id", "reports", ["reporter_user_id"])
    op.create_index("ix_reports_target_user_id", "reports", ["target_user_id"])
    op.create_index("ix_reports_target_listing_id", "reports", ["target_listing_id"])
    op.create_index("ix_reports_status_severity", "reports", ["status", "severity"])

    op.create_table(
        "moderation_cases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "report_id",
            sa.Integer(),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_moderator_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="open"),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column(
            "evidence_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('open', 'in_review', 'actioned', 'closed', 'appealed')",
            name="status",
        ),
        sa.CheckConstraint(
            "severity in ('low', 'medium', 'high', 'critical')",
            name="severity",
        ),
        sa.UniqueConstraint("public_id", name="uq_moderation_cases_public_id"),
        sa.UniqueConstraint("report_id", name="uq_moderation_cases_report_id"),
    )
    op.create_index(
        "ix_moderation_cases_queue",
        "moderation_cases",
        ["status", "priority_score", "created_at"],
    )
    op.create_index(
        "ix_moderation_cases_assigned_moderator_user_id",
        "moderation_cases",
        ["assigned_moderator_user_id"],
    )

    op.create_table(
        "moderation_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "case_id",
            sa.Integer(),
            sa.ForeignKey("moderation_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "moderator_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("duration_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "evidence_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "action_type in "
            "('warn', 'remove_content', 'suspend', 'ban', 'dismiss', 'restore', "
            "'appeal_submitted', 'note')",
            name="action_type",
        ),
        sa.UniqueConstraint("public_id", name="uq_moderation_actions_public_id"),
    )
    op.create_index(
        "ix_moderation_actions_case_id",
        "moderation_actions",
        ["case_id"],
    )
    op.create_index(
        "ix_moderation_actions_moderator_user_id",
        "moderation_actions",
        ["moderator_user_id"],
    )

    op.create_table(
        "risk_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "report_id",
            sa.Integer(),
            sa.ForeignKey("reports.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="open"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "severity in ('low', 'medium', 'high', 'critical')",
            name="severity",
        ),
        sa.CheckConstraint("status in ('open', 'reviewed', 'cleared')", name="status"),
        sa.CheckConstraint("score >= 0 and score <= 100", name="score_range"),
        sa.UniqueConstraint("public_id", name="uq_risk_events_public_id"),
    )
    op.create_index("ix_risk_events_user_status", "risk_events", ["user_id", "status"])
    op.create_index("ix_risk_events_event_type", "risk_events", ["event_type"])

    op.create_table(
        "device_risk",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("device_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "reasons_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "risk_level in ('low', 'medium', 'high', 'blocked')",
            name="risk_level",
        ),
        sa.CheckConstraint("score >= 0 and score <= 100", name="score_range"),
        sa.UniqueConstraint("public_id", name="uq_device_risk_public_id"),
        sa.UniqueConstraint("device_fingerprint", name="uq_device_risk_fingerprint"),
    )
    op.create_index("ix_device_risk_user_id", "device_risk", ["user_id"])
    op.create_index("ix_device_risk_risk_level", "device_risk", ["risk_level"])

    op.create_table(
        "copyright_claims",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "report_id",
            sa.Integer(),
            sa.ForeignKey("reports.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("claimant_email", sa.String(length=320), nullable=False),
        sa.Column("work_title", sa.String(length=500), nullable=False),
        sa.Column("claimant_statement", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="submitted"),
        sa.Column(
            "evidence_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('submitted', 'reviewing', 'actioned', 'rejected')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_copyright_claims_public_id"),
    )
    op.create_index("ix_copyright_claims_status", "copyright_claims", ["status"])
    op.create_index("ix_copyright_claims_report_id", "copyright_claims", ["report_id"])


def downgrade() -> None:
    op.drop_index("ix_copyright_claims_report_id", table_name="copyright_claims")
    op.drop_index("ix_copyright_claims_status", table_name="copyright_claims")
    op.drop_table("copyright_claims")
    op.drop_index("ix_device_risk_risk_level", table_name="device_risk")
    op.drop_index("ix_device_risk_user_id", table_name="device_risk")
    op.drop_table("device_risk")
    op.drop_index("ix_risk_events_event_type", table_name="risk_events")
    op.drop_index("ix_risk_events_user_status", table_name="risk_events")
    op.drop_table("risk_events")
    op.drop_index("ix_moderation_actions_moderator_user_id", table_name="moderation_actions")
    op.drop_index("ix_moderation_actions_case_id", table_name="moderation_actions")
    op.drop_table("moderation_actions")
    op.drop_index(
        "ix_moderation_cases_assigned_moderator_user_id",
        table_name="moderation_cases",
    )
    op.drop_index("ix_moderation_cases_queue", table_name="moderation_cases")
    op.drop_table("moderation_cases")
    op.drop_index("ix_reports_status_severity", table_name="reports")
    op.drop_index("ix_reports_target_listing_id", table_name="reports")
    op.drop_index("ix_reports_target_user_id", table_name="reports")
    op.drop_index("ix_reports_reporter_user_id", table_name="reports")
    op.drop_table("reports")
