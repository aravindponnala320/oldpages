from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oldpages_api.identity.models import User
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class DonationCampaign(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "donation_campaigns"
    __table_args__ = (
        CheckConstraint(
            "status in ('draft', 'active', 'paused', 'completed', 'cancelled')",
            name="status",
        ),
        CheckConstraint("quantity_target > 0", name="quantity_target_positive"),
        CheckConstraint("quantity_pledged >= 0", name="quantity_pledged_non_negative"),
        CheckConstraint("quantity_received >= 0", name="quantity_received_non_negative"),
        Index("ix_donation_campaigns_created_by_user_id", "created_by_user_id"),
        Index("ix_donation_campaigns_institution_id", "institution_id"),
        Index("ix_donation_campaigns_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    institution_id: Mapped[int | None] = mapped_column(
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    accepted_conditions_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    quantity_target: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_pledged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pickup_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dropoff_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str] = mapped_column(String(4), nullable=False, default="IN")

    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    needs: Mapped[list[DonationNeed]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    pledges: Mapped[list[DonationPledge]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )


class DonationNeed(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "donation_needs"
    __table_args__ = (
        CheckConstraint("quantity_needed > 0", name="quantity_needed_positive"),
        CheckConstraint("quantity_pledged >= 0", name="quantity_pledged_non_negative"),
        Index("ix_donation_needs_campaign_id", "campaign_id"),
        Index("ix_donation_needs_book_id", "book_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("donation_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    book_id: Mapped[int | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quantity_needed: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_pledged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    campaign: Mapped[DonationCampaign] = relationship(back_populates="needs")


class DonationPledge(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "donation_pledges"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'accepted', 'pickup_scheduled', 'received', 'cancelled')",
            name="status",
        ),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_donation_pledges_campaign_id", "campaign_id"),
        Index("ix_donation_pledges_donor_user_id", "donor_user_id"),
        Index("ix_donation_pledges_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("donation_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    donor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    donation_need_id: Mapped[int | None] = mapped_column(
        ForeignKey("donation_needs.id", ondelete="SET NULL"),
        nullable=True,
    )
    title_snapshot: Mapped[str] = mapped_column(String(500), nullable=False)
    condition: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped[DonationCampaign] = relationship(back_populates="pledges")
    donor: Mapped[User] = relationship(foreign_keys=[donor_user_id])
    donation_need: Mapped[DonationNeed | None] = relationship()
    receipt: Mapped[DonationReceipt | None] = relationship(
        back_populates="pledge",
        uselist=False,
    )


class DonationReceipt(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "donation_receipts"
    __table_args__ = (
        UniqueConstraint("pledge_id", name="uq_donation_receipts_pledge_id"),
        Index("ix_donation_receipts_campaign_id", "campaign_id"),
        Index("ix_donation_receipts_issued_by_user_id", "issued_by_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pledge_id: Mapped[int] = mapped_column(
        ForeignKey("donation_pledges.id", ondelete="CASCADE"),
        nullable=False,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("donation_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    issued_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    receipt_text: Mapped[str] = mapped_column(Text, nullable=False)
    impact_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    campaign: Mapped[DonationCampaign] = relationship()
    issued_by: Mapped[User] = relationship(foreign_keys=[issued_by_user_id])
    pledge: Mapped[DonationPledge] = relationship(back_populates="receipt")


__all__ = [
    "DonationCampaign",
    "DonationNeed",
    "DonationPledge",
    "DonationReceipt",
]
