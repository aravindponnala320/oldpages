"""Create institution and donation tables.

Revision ID: 0013_institutions_donations
Revises: 0012_payments_orders_shipping
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_institutions_donations"
down_revision: str | None = "0012_payments_orders_shipping"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("slug", sa.String(length=260), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=4), nullable=False, server_default="IN"),
        sa.Column("latitude", sa.String(length=40), nullable=True),
        sa.Column("longitude", sa.String(length=40), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type in ('school', 'college', 'university', 'library', 'ngo', 'coaching',"
            " 'publisher', 'bookstore', 'other')",
            name="type",
        ),
        sa.CheckConstraint("status in ('pending', 'active', 'suspended')", name="status"),
        sa.CheckConstraint("member_count >= 0", name="member_count_non_negative"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_institutions_slug", "institutions", ["slug"])
    op.create_index("ix_institutions_type_status", "institutions", ["type", "status"])
    op.create_index("ix_institutions_owner_user_id", "institutions", ["owner_user_id"])

    op.create_table(
        "institution_domains",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(length=253), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_index(
        "ix_institution_domains_institution_id", "institution_domains", ["institution_id"]
    )

    op.create_table(
        "institution_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False, server_default="member"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role in ('admin', 'staff', 'student', 'alumni', 'member')", name="role"
        ),
        sa.CheckConstraint("status in ('pending', 'active', 'suspended')", name="status"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("institution_id", "user_id", name="uq_institution_members_inst_user"),
    )
    op.create_index(
        "ix_institution_members_institution_id", "institution_members", ["institution_id"]
    )
    op.create_index("ix_institution_members_user_id", "institution_members", ["user_id"])

    op.create_table(
        "donation_campaigns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("institution_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("accepted_conditions_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("quantity_target", sa.Integer(), nullable=False),
        sa.Column("quantity_pledged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quantity_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pickup_address", sa.String(length=500), nullable=True),
        sa.Column("dropoff_address", sa.String(length=500), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="draft"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=4), nullable=False, server_default="IN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('draft', 'active', 'paused', 'completed', 'cancelled')", name="status"
        ),
        sa.CheckConstraint("quantity_target > 0", name="quantity_target_positive"),
        sa.CheckConstraint("quantity_pledged >= 0", name="quantity_pledged_non_negative"),
        sa.CheckConstraint("quantity_received >= 0", name="quantity_received_non_negative"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_donation_campaigns_created_by_user_id",
        "donation_campaigns",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_donation_campaigns_institution_id", "donation_campaigns", ["institution_id"]
    )
    op.create_index("ix_donation_campaigns_status", "donation_campaigns", ["status"])

    op.create_table(
        "donation_needs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("author", sa.String(length=500), nullable=True),
        sa.Column("quantity_needed", sa.Integer(), nullable=False),
        sa.Column("quantity_pledged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity_needed > 0", name="quantity_needed_positive"),
        sa.CheckConstraint("quantity_pledged >= 0", name="quantity_pledged_non_negative"),
        sa.ForeignKeyConstraint(["campaign_id"], ["donation_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_donation_needs_campaign_id", "donation_needs", ["campaign_id"])
    op.create_index("ix_donation_needs_book_id", "donation_needs", ["book_id"])

    op.create_table(
        "donation_pledges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("donor_user_id", sa.Integer(), nullable=False),
        sa.Column("donation_need_id", sa.Integer(), nullable=True),
        sa.Column("title_snapshot", sa.String(length=500), nullable=False),
        sa.Column("condition", sa.String(length=80), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('pending', 'accepted', 'pickup_scheduled', 'received', 'cancelled')",
            name="status",
        ),
        sa.CheckConstraint("quantity > 0", name="quantity_positive"),
        sa.ForeignKeyConstraint(["campaign_id"], ["donation_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["donor_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["donation_need_id"], ["donation_needs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_donation_pledges_campaign_id", "donation_pledges", ["campaign_id"])
    op.create_index("ix_donation_pledges_donor_user_id", "donation_pledges", ["donor_user_id"])
    op.create_index("ix_donation_pledges_status", "donation_pledges", ["status"])

    op.create_table(
        "donation_receipts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("pledge_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("issued_by_user_id", sa.Integer(), nullable=False),
        sa.Column("receipt_text", sa.Text(), nullable=False),
        sa.Column("impact_note", sa.Text(), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pledge_id"], ["donation_pledges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["donation_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["issued_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("pledge_id", name="uq_donation_receipts_pledge_id"),
    )
    op.create_index("ix_donation_receipts_campaign_id", "donation_receipts", ["campaign_id"])
    op.create_index(
        "ix_donation_receipts_issued_by_user_id", "donation_receipts", ["issued_by_user_id"]
    )


def downgrade() -> None:
    op.drop_table("donation_receipts")
    op.drop_table("donation_pledges")
    op.drop_table("donation_needs")
    op.drop_table("donation_campaigns")
    op.drop_table("institution_members")
    op.drop_table("institution_domains")
    op.drop_table("institutions")
