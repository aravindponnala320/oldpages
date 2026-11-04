"""Create commerce tables.

Revision ID: 0007_commerce
Revises: 0006_chat_notifications
Create Date: 2026-06-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_commerce"
down_revision: str | None = "0006_chat_notifications"
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
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "buyer_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "seller_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "proposer_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_offer_id",
            sa.Integer(),
            sa.ForeignKey("offers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("offer_type", sa.String(length=24), nullable=False, server_default="price"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "fulfillment_method", sa.String(length=24), nullable=False, server_default="pickup"
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "bundle_listing_ids_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "offer_type in ('price', 'counter', 'exchange', 'bundle')",
            name="offer_type",
        ),
        sa.CheckConstraint(
            "status in ('pending', 'countered', 'accepted', 'rejected', 'withdrawn', 'expired')",
            name="status",
        ),
        sa.CheckConstraint("quantity > 0", name="quantity_positive"),
        sa.CheckConstraint(
            "amount_cents is null or amount_cents >= 0",
            name="amount_non_negative",
        ),
        sa.CheckConstraint(
            "fulfillment_method in ('pickup', 'shipping')",
            name="fulfillment_method",
        ),
        sa.UniqueConstraint("public_id", name="uq_offers_public_id"),
    )
    op.create_index("ix_offers_listing_status", "offers", ["listing_id", "status"])
    op.create_index("ix_offers_buyer_user_id", "offers", ["buyer_user_id"])
    op.create_index("ix_offers_seller_user_id", "offers", ["seller_user_id"])
    op.create_index("ix_offers_expires_at", "offers", ["expires_at"])

    op.create_table(
        "exchange_offer_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "offer_id",
            sa.Integer(),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "offered_listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("condition_note", sa.String(length=500), nullable=True),
        sa.Column("cash_adjustment_cents", sa.Integer(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "cash_adjustment_cents is null or cash_adjustment_cents >= 0",
            name="cash_adjustment_non_negative",
        ),
        sa.UniqueConstraint("public_id", name="uq_exchange_offer_items_public_id"),
    )
    op.create_index(
        "ix_exchange_offer_items_offer_id",
        "exchange_offer_items",
        ["offer_id"],
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "offer_id",
            sa.Integer(),
            sa.ForeignKey("offers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "buyer_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "seller_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="reserved"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column(
            "fulfillment_method", sa.String(length=24), nullable=False, server_default="pickup"
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('reserved', 'ready_for_pickup', 'completed', 'cancelled', 'disputed')",
            name="status",
        ),
        sa.CheckConstraint(
            "fulfillment_method in ('pickup', 'shipping')",
            name="fulfillment_method",
        ),
        sa.CheckConstraint("quantity > 0", name="quantity_positive"),
        sa.CheckConstraint(
            "amount_cents is null or amount_cents >= 0",
            name="amount_non_negative",
        ),
        sa.UniqueConstraint("public_id", name="uq_transactions_public_id"),
        sa.UniqueConstraint("offer_id", name="uq_transactions_offer_id"),
    )
    op.create_index("ix_transactions_buyer_status", "transactions", ["buyer_user_id", "status"])
    op.create_index("ix_transactions_seller_status", "transactions", ["seller_user_id", "status"])
    op.create_index("ix_transactions_listing_id", "transactions", ["listing_id"])

    op.create_table(
        "pickup_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "proposed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "confirmed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="proposed"),
        sa.Column("proposed_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proposed_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("public_location_label", sa.String(length=240), nullable=False),
        sa.Column("exact_address", sa.String(length=500), nullable=True),
        sa.Column("exact_latitude", sa.String(length=40), nullable=True),
        sa.Column("exact_longitude", sa.String(length=40), nullable=True),
        sa.Column("pickup_notes_private", sa.Text(), nullable=True),
        sa.Column("handover_code", sa.String(length=12), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('proposed', 'confirmed', 'completed', 'cancelled')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_pickup_sessions_public_id"),
        sa.UniqueConstraint("transaction_id", name="uq_pickup_sessions_transaction_id"),
    )
    op.create_index("ix_pickup_sessions_status", "pickup_sessions", ["status"])
    op.create_index(
        "ix_pickup_sessions_proposed_start_at",
        "pickup_sessions",
        ["proposed_start_at"],
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewee_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("review_type", sa.String(length=40), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="published"),
        *timestamps(),
        sa.CheckConstraint("rating >= 1 and rating <= 5", name="rating_range"),
        sa.CheckConstraint(
            "review_type in ('buyer_reviews_seller', 'seller_reviews_buyer')",
            name="review_type",
        ),
        sa.CheckConstraint(
            "status in ('published', 'hidden', 'removed')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_reviews_public_id"),
        sa.UniqueConstraint(
            "transaction_id",
            "reviewer_user_id",
            name="uq_reviews_once_per_side",
        ),
    )
    op.create_index("ix_reviews_reviewee_user_id", "reviews", ["reviewee_user_id"])
    op.create_index("ix_reviews_transaction_id", "reviews", ["transaction_id"])

    op.create_table(
        "review_dimensions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "review_id",
            sa.Integer(),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dimension", sa.String(length=80), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        *timestamps(),
        sa.CheckConstraint("rating >= 1 and rating <= 5", name="rating_range"),
        sa.UniqueConstraint("public_id", name="uq_review_dimensions_public_id"),
        sa.UniqueConstraint(
            "review_id",
            "dimension",
            name="uq_review_dimensions_dimension",
        ),
    )


def downgrade() -> None:
    op.drop_table("review_dimensions")
    op.drop_index("ix_reviews_transaction_id", table_name="reviews")
    op.drop_index("ix_reviews_reviewee_user_id", table_name="reviews")
    op.drop_table("reviews")
    op.drop_index("ix_pickup_sessions_proposed_start_at", table_name="pickup_sessions")
    op.drop_index("ix_pickup_sessions_status", table_name="pickup_sessions")
    op.drop_table("pickup_sessions")
    op.drop_index("ix_transactions_listing_id", table_name="transactions")
    op.drop_index("ix_transactions_seller_status", table_name="transactions")
    op.drop_index("ix_transactions_buyer_status", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_exchange_offer_items_offer_id", table_name="exchange_offer_items")
    op.drop_table("exchange_offer_items")
    op.drop_index("ix_offers_expires_at", table_name="offers")
    op.drop_index("ix_offers_seller_user_id", table_name="offers")
    op.drop_index("ix_offers_buyer_user_id", table_name="offers")
    op.drop_index("ix_offers_listing_status", table_name="offers")
    op.drop_table("offers")
