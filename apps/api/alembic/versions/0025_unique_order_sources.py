"""One order per cart and per accepted offer.

A retried checkout, or both parties creating an order from the same offer, used to make a
second order for the same books. Existing duplicates keep their rows; only the earliest order
keeps the link to its cart or offer, so the unique constraints can be added.

Revision ID: 0025_unique_order_sources
Revises: 0024_search_text_indexes
"""

from __future__ import annotations

from alembic import op

revision: str = "0025_unique_order_sources"
down_revision: str | None = "0024_search_text_indexes"
branch_labels: str | None = None
depends_on: str | None = None

COLUMNS = (
    ("cart_id", "uq_orders_cart_id", "ix_orders_cart_id"),
    ("offer_id", "uq_orders_offer_id", "ix_orders_offer_id"),
)


def upgrade() -> None:
    for column, constraint, index in COLUMNS:
        # column comes from COLUMNS above, never from input.
        op.execute(
            f"UPDATE orders SET {column} = NULL WHERE {column} IS NOT NULL"  # noqa: S608
            f" AND id NOT IN (SELECT min(id) FROM orders WHERE {column} IS NOT NULL"
            f" GROUP BY {column})"
        )
        op.drop_index(index, table_name="orders")
        op.create_unique_constraint(constraint, "orders", [column])


def downgrade() -> None:
    for column, constraint, index in COLUMNS:
        op.drop_constraint(constraint, "orders", type_="unique")
        op.create_index(index, "orders", [column])
