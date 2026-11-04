from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Book(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "books"
    __table_args__ = (
        Index("ix_books_normalized_title", "normalized_title"),
        Index("ix_books_original_language", "original_language"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(500), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_language: Mapped[str | None] = mapped_column(String(24), nullable=True)

    authors: Mapped[list[BookAuthor]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )
    categories: Mapped[list[BookCategory]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )
    editions: Mapped[list[BookEdition]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )


class BookEdition(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "book_editions"
    __table_args__ = (
        CheckConstraint("page_count is null or page_count > 0", name="page_count_positive"),
        CheckConstraint(
            "publication_year is null or (publication_year >= 1450 and publication_year <= 2200)",
            name="publication_year_range",
        ),
        CheckConstraint(
            "format in "
            "('paperback', 'hardcover', 'ebook', 'audiobook', 'spiral_bound', "
            "'loose_leaf', 'unknown')",
            name="format",
        ),
        CheckConstraint(
            "metadata_status in ('needs_review', 'verified')",
            name="metadata_status",
        ),
        UniqueConstraint("edition_fingerprint", name="uq_book_editions_fingerprint"),
        Index("ix_book_editions_book_id", "book_id"),
        Index("ix_book_editions_title", "title"),
        Index("ix_book_editions_language", "language"),
        Index("ix_book_editions_publisher_id", "publisher_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    publisher_id: Mapped[int | None] = mapped_column(
        ForeignKey("publishers.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    edition: Mapped[str | None] = mapped_column(String(120), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(24), nullable=False, default="en")
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    format: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    genres: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    subjects: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    external_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    edition_fingerprint: Mapped[str] = mapped_column(String(512), nullable=False)
    metadata_status: Mapped[str] = mapped_column(String(32), nullable=False, default="needs_review")

    academic_metadata: Mapped[AcademicMetadata | None] = relationship(
        back_populates="book_edition",
        cascade="all, delete-orphan",
        uselist=False,
    )
    book: Mapped[Book] = relationship(back_populates="editions")
    identifiers: Mapped[list[BookIdentifier]] = relationship(
        back_populates="book_edition",
        cascade="all, delete-orphan",
    )
    publisher: Mapped[Publisher | None] = relationship(back_populates="editions")


class Author(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "authors"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_authors_normalized_name"),
        Index("ix_authors_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(240), nullable=False)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)

    books: Mapped[list[BookAuthor]] = relationship(back_populates="author")


class BookAuthor(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "book_authors"
    __table_args__ = (
        CheckConstraint(
            "role in ('author', 'editor', 'translator', 'illustrator', 'contributor')",
            name="role",
        ),
        UniqueConstraint("book_id", "author_id", "role", name="uq_book_authors_role"),
        Index("ix_book_authors_author_id", "author_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="RESTRICT"))
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="author")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    author: Mapped[Author] = relationship(back_populates="books")
    book: Mapped[Book] = relationship(back_populates="authors")


class Publisher(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "publishers"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_publishers_normalized_name"),
        Index("ix_publishers_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(240), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    editions: Mapped[list[BookEdition]] = relationship(back_populates="publisher")


class Category(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_categories_slug"),
        Index("ix_categories_parent_id", "parent_id"),
        Index("ix_categories_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    books: Mapped[list[BookCategory]] = relationship(back_populates="category")
    children: Mapped[list[Category]] = relationship(back_populates="parent")
    parent: Mapped[Category | None] = relationship(
        back_populates="children",
        remote_side="Category.id",
    )


class BookCategory(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "book_categories"
    __table_args__ = (
        UniqueConstraint("book_id", "category_id", name="uq_book_categories_pair"),
        Index("ix_book_categories_category_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))

    book: Mapped[Book] = relationship(back_populates="categories")
    category: Mapped[Category] = relationship(back_populates="books")


class BookIdentifier(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "book_identifiers"
    __table_args__ = (
        CheckConstraint(
            "identifier_type in ('isbn10', 'isbn13', 'open_library', 'google_books', 'other')",
            name="identifier_type",
        ),
        UniqueConstraint("identifier_type", "identifier_value", name="uq_book_identifiers_value"),
        Index("ix_book_identifiers_edition_id", "book_edition_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_edition_id: Mapped[int] = mapped_column(ForeignKey("book_editions.id", ondelete="CASCADE"))
    identifier_type: Mapped[str] = mapped_column(String(40), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="manual")

    book_edition: Mapped[BookEdition] = relationship(back_populates="identifiers")


class AcademicMetadata(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "academic_metadata"
    __table_args__ = (
        UniqueConstraint("book_edition_id", name="uq_academic_metadata_book_edition_id"),
        Index("ix_academic_metadata_school_board", "school_board"),
        Index("ix_academic_metadata_course", "course"),
        Index("ix_academic_metadata_exam", "exam"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_edition_id: Mapped[int] = mapped_column(ForeignKey("book_editions.id", ondelete="CASCADE"))
    school_board: Mapped[str | None] = mapped_column(String(120), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(160), nullable=True)
    college: Mapped[str | None] = mapped_column(String(180), nullable=True)
    university: Mapped[str | None] = mapped_column(String(180), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(120), nullable=True)
    department: Mapped[str | None] = mapped_column(String(160), nullable=True)
    course: Mapped[str | None] = mapped_column(String(160), nullable=True)
    semester: Mapped[str | None] = mapped_column(String(40), nullable=True)
    professor: Mapped[str | None] = mapped_column(String(160), nullable=True)
    exam: Mapped[str | None] = mapped_column(String(160), nullable=True)
    exam_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    syllabus_version: Mapped[str | None] = mapped_column(String(80), nullable=True)

    book_edition: Mapped[BookEdition] = relationship(back_populates="academic_metadata")
