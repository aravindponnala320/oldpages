"""Add approval workflow to institutions and business_profiles.

Revision ID: 0018_approval_workflow
Revises: 0017_fix_timestamp_defaults
Create Date: 2026-08-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_approval_workflow"
down_revision: str | None = "0017_fix_timestamp_defaults"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # institutions: add rejected status + review fields
    op.drop_constraint("status", "institutions", type_="check")
    op.create_check_constraint(
        "status",
        "institutions",
        "status in ('pending', 'active', 'suspended', 'rejected')",
    )
    op.add_column("institutions", sa.Column("rejected_reason", sa.Text(), nullable=True))
    op.add_column(
        "institutions",
        sa.Column(
            "reviewed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "institutions",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_institutions_status",
        "institutions",
        ["status"],
    )

    # business_profiles: add rejected status + review fields
    op.drop_constraint("status", "business_profiles", type_="check")
    op.create_check_constraint(
        "status",
        "business_profiles",
        "status in ('pending', 'active', 'suspended', 'rejected')",
    )
    op.add_column("business_profiles", sa.Column("rejected_reason", sa.Text(), nullable=True))
    op.add_column(
        "business_profiles",
        sa.Column(
            "reviewed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "business_profiles",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_business_profiles_status",
        "business_profiles",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_institutions_status", "institutions")
    op.drop_column("institutions", "reviewed_at")
    op.drop_column("institutions", "reviewed_by_user_id")
    op.drop_column("institutions", "rejected_reason")
    op.drop_constraint("status", "institutions", type_="check")
    op.create_check_constraint(
        "status",
        "institutions",
        "status in ('pending', 'active', 'suspended')",
    )

    op.drop_index("ix_business_profiles_status", "business_profiles")
    op.drop_column("business_profiles", "reviewed_at")
    op.drop_column("business_profiles", "reviewed_by_user_id")
    op.drop_column("business_profiles", "rejected_reason")
    op.drop_constraint("status", "business_profiles", type_="check")
    op.create_check_constraint(
        "status",
        "business_profiles",
        "status in ('pending', 'active', 'suspended')",
    )
