"""Create book catalog tables.

Revision ID: 0003_catalog
Revises: 0002_identity_profiles
Create Date: 2026-06-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_catalog"
down_revision: str | None = "0002_identity_profiles"
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


def jsonb_array() -> sa.ColumnElement:
    return sa.text("'[]'::jsonb")


def jsonb_object() -> sa.ColumnElement:
    return sa.text("'{}'::jsonb")


def upgrade() -> None:
    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("normalized_name", sa.String(length=240), nullable=False),
        sa.Column("biography", sa.Text(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_authors_public_id"),
        sa.UniqueConstraint("normalized_name", name="uq_authors_normalized_name"),
    )
    op.create_index("ix_authors_name", "authors", ["name"])

    op.create_table(
        "publishers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("normalized_name", sa.String(length=240), nullable=False),
        sa.Column("website_url", sa.String(length=1000), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_publishers_public_id"),
        sa.UniqueConstraint("normalized_name", name="uq_publishers_normalized_name"),
    )
    op.create_index("ix_publishers_name", "publishers", ["name"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_categories_public_id"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_index("ix_categories_is_active", "categories", ["is_active"])

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("normalized_title", sa.String(length=500), nullable=False),
        sa.Column("subtitle", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("original_language", sa.String(length=24), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_books_public_id"),
    )
    op.create_index("ix_books_normalized_title", "books", ["normalized_title"])
    op.create_index("ix_books_original_language", "books", ["original_language"])

    op.create_table(
        "book_editions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "book_id", sa.Integer(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "publisher_id",
            sa.Integer(),
            sa.ForeignKey("publishers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("subtitle", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("edition", sa.String(length=120), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=24), nullable=False, server_default="en"),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("format", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("cover_image_url", sa.String(length=1000), nullable=True),
        sa.Column(
            "genres",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        sa.Column(
            "subjects",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        sa.Column(
            "external_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("edition_fingerprint", sa.String(length=512), nullable=False),
        sa.Column(
            "metadata_status",
            sa.String(length=32),
            nullable=False,
            server_default="needs_review",
        ),
        *timestamps(),
        sa.CheckConstraint("page_count is null or page_count > 0", name="page_count_positive"),
        sa.CheckConstraint(
            "publication_year is null or (publication_year >= 1450 and publication_year <= 2200)",
            name="publication_year_range",
        ),
        sa.CheckConstraint(
            "format in "
            "('paperback', 'hardcover', 'ebook', 'audiobook', 'spiral_bound', "
            "'loose_leaf', 'unknown')",
            name="format",
        ),
        sa.CheckConstraint(
            "metadata_status in ('needs_review', 'verified')", name="metadata_status"
        ),
        sa.UniqueConstraint("public_id", name="uq_book_editions_public_id"),
        sa.UniqueConstraint("edition_fingerprint", name="uq_book_editions_fingerprint"),
    )
    op.create_index("ix_book_editions_book_id", "book_editions", ["book_id"])
    op.create_index("ix_book_editions_title", "book_editions", ["title"])
    op.create_index("ix_book_editions_language", "book_editions", ["language"])
    op.create_index("ix_book_editions_publisher_id", "book_editions", ["publisher_id"])

    op.create_table(
        "book_authors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "book_id", sa.Integer(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "author_id",
            sa.Integer(),
            sa.ForeignKey("authors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="author"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.CheckConstraint(
            "role in ('author', 'editor', 'translator', 'illustrator', 'contributor')",
            name="role",
        ),
        sa.UniqueConstraint("public_id", name="uq_book_authors_public_id"),
        sa.UniqueConstraint("book_id", "author_id", "role", name="uq_book_authors_role"),
    )
    op.create_index("ix_book_authors_author_id", "book_authors", ["author_id"])

    op.create_table(
        "book_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "book_id", sa.Integer(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_book_categories_public_id"),
        sa.UniqueConstraint("book_id", "category_id", name="uq_book_categories_pair"),
    )
    op.create_index("ix_book_categories_category_id", "book_categories", ["category_id"])

    op.create_table(
        "book_identifiers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("identifier_type", sa.String(length=40), nullable=False),
        sa.Column("identifier_value", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="manual"),
        *timestamps(),
        sa.CheckConstraint(
            "identifier_type in ('isbn10', 'isbn13', 'open_library', 'google_books', 'other')",
            name="identifier_type",
        ),
        sa.UniqueConstraint("public_id", name="uq_book_identifiers_public_id"),
        sa.UniqueConstraint(
            "identifier_type", "identifier_value", name="uq_book_identifiers_value"
        ),
    )
    op.create_index("ix_book_identifiers_edition_id", "book_identifiers", ["book_edition_id"])

    op.create_table(
        "academic_metadata",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("school_board", sa.String(length=120), nullable=True),
        sa.Column("grade", sa.String(length=40), nullable=True),
        sa.Column("subject", sa.String(length=160), nullable=True),
        sa.Column("college", sa.String(length=180), nullable=True),
        sa.Column("university", sa.String(length=180), nullable=True),
        sa.Column("degree", sa.String(length=120), nullable=True),
        sa.Column("department", sa.String(length=160), nullable=True),
        sa.Column("course", sa.String(length=160), nullable=True),
        sa.Column("semester", sa.String(length=40), nullable=True),
        sa.Column("professor", sa.String(length=160), nullable=True),
        sa.Column("exam", sa.String(length=160), nullable=True),
        sa.Column("exam_year", sa.Integer(), nullable=True),
        sa.Column("syllabus_version", sa.String(length=80), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_academic_metadata_public_id"),
        sa.UniqueConstraint("book_edition_id", name="uq_academic_metadata_book_edition_id"),
    )
    op.create_index("ix_academic_metadata_school_board", "academic_metadata", ["school_board"])
    op.create_index("ix_academic_metadata_course", "academic_metadata", ["course"])
    op.create_index("ix_academic_metadata_exam", "academic_metadata", ["exam"])


def downgrade() -> None:
    op.drop_index("ix_academic_metadata_exam", table_name="academic_metadata")
    op.drop_index("ix_academic_metadata_course", table_name="academic_metadata")
    op.drop_index("ix_academic_metadata_school_board", table_name="academic_metadata")
    op.drop_table("academic_metadata")
    op.drop_index("ix_book_identifiers_edition_id", table_name="book_identifiers")
    op.drop_table("book_identifiers")
    op.drop_index("ix_book_categories_category_id", table_name="book_categories")
    op.drop_table("book_categories")
    op.drop_index("ix_book_authors_author_id", table_name="book_authors")
    op.drop_table("book_authors")
    op.drop_index("ix_book_editions_publisher_id", table_name="book_editions")
    op.drop_index("ix_book_editions_language", table_name="book_editions")
    op.drop_index("ix_book_editions_title", table_name="book_editions")
    op.drop_index("ix_book_editions_book_id", table_name="book_editions")
    op.drop_table("book_editions")
    op.drop_index("ix_books_original_language", table_name="books")
    op.drop_index("ix_books_normalized_title", table_name="books")
    op.drop_table("books")
    op.drop_index("ix_categories_is_active", table_name="categories")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_publishers_name", table_name="publishers")
    op.drop_table("publishers")
    op.drop_index("ix_authors_name", table_name="authors")
    op.drop_table("authors")
