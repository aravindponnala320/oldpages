from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
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

from oldpages_api.chat.models import Message
from oldpages_api.commerce.models import Review
from oldpages_api.identity.models import User
from oldpages_api.listings.models import Listing
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Report(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "target_type in ('user', 'listing', 'message', 'review', 'copyright')",
            name="target_type",
        ),
        CheckConstraint(
            "severity in ('low', 'medium', 'high', 'critical')",
            name="severity",
        ),
        CheckConstraint(
            "status in ('open', 'in_review', 'resolved', 'dismissed', 'appealed')",
            name="status",
        ),
        Index("ix_reports_reporter_user_id", "reporter_user_id"),
        Index("ix_reports_target_user_id", "target_user_id"),
        Index("ix_reports_target_listing_id", "target_listing_id"),
        Index("ix_reports_status_severity", "status", "severity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_type: Mapped[str] = mapped_column(String(24), nullable=False)
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_review_id: Mapped[int | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="SET NULL"),
        nullable=True,
    )

    case: Mapped[ModerationCase | None] = relationship(back_populates="report", uselist=False)
    reporter: Mapped[User] = relationship(foreign_keys=[reporter_user_id])
    target_listing: Mapped[Listing | None] = relationship()
    target_message: Mapped[Message | None] = relationship()
    target_review: Mapped[Review | None] = relationship()
    target_user: Mapped[User | None] = relationship(foreign_keys=[target_user_id])


class ModerationCase(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "moderation_cases"
    __table_args__ = (
        CheckConstraint(
            "status in ('open', 'in_review', 'actioned', 'closed', 'appealed')",
            name="status",
        ),
        CheckConstraint(
            "severity in ('low', 'medium', 'high', 'critical')",
            name="severity",
        ),
        UniqueConstraint("report_id", name="uq_moderation_cases_report_id"),
        Index("ix_moderation_cases_queue", "status", "priority_score", "created_at"),
        Index("ix_moderation_cases_assigned_moderator_user_id", "assigned_moderator_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"))
    assigned_moderator_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    evidence_snapshot_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    actions: Mapped[list[ModerationAction]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    assigned_moderator: Mapped[User | None] = relationship()
    report: Mapped[Report] = relationship(back_populates="case")


class ModerationAction(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "moderation_actions"
    __table_args__ = (
        CheckConstraint(
            "action_type in "
            "('warn', 'remove_content', 'suspend', 'ban', 'dismiss', 'restore', "
            "'appeal_submitted', 'note')",
            name="action_type",
        ),
        Index("ix_moderation_actions_case_id", "case_id"),
        Index("ix_moderation_actions_moderator_user_id", "moderator_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("moderation_cases.id", ondelete="CASCADE"))
    moderator_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_snapshot_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    actor: Mapped[User | None] = relationship(foreign_keys=[actor_user_id])
    case: Mapped[ModerationCase] = relationship(back_populates="actions")
    moderator: Mapped[User | None] = relationship(foreign_keys=[moderator_user_id])


class RiskEvent(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "risk_events"
    __table_args__ = (
        CheckConstraint(
            "severity in ('low', 'medium', 'high', 'critical')",
            name="severity",
        ),
        CheckConstraint(
            "status in ('open', 'reviewed', 'cleared')",
            name="status",
        ),
        CheckConstraint("score >= 0 and score <= 100", name="score_range"),
        Index("ix_risk_events_user_status", "user_id", "status"),
        Index("ix_risk_events_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    report_id: Mapped[int | None] = mapped_column(
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    report: Mapped[Report | None] = relationship()
    user: Mapped[User | None] = relationship()


class DeviceRisk(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "device_risk"
    __table_args__ = (
        CheckConstraint(
            "risk_level in ('low', 'medium', 'high', 'blocked')",
            name="risk_level",
        ),
        CheckConstraint("score >= 0 and score <= 100", name="score_range"),
        UniqueConstraint("device_fingerprint", name="uq_device_risk_fingerprint"),
        Index("ix_device_risk_user_id", "user_id"),
        Index("ix_device_risk_risk_level", "risk_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    device_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, default="low")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasons_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship()


class CopyrightClaim(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "copyright_claims"
    __table_args__ = (
        CheckConstraint(
            "status in ('submitted', 'reviewing', 'actioned', 'rejected')",
            name="status",
        ),
        Index("ix_copyright_claims_status", "status"),
        Index("ix_copyright_claims_report_id", "report_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int | None] = mapped_column(
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    claimant_email: Mapped[str] = mapped_column(String(320), nullable=False)
    work_title: Mapped[str] = mapped_column(String(500), nullable=False)
    claimant_statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="submitted")
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    report: Mapped[Report | None] = relationship()


__all__ = [
    "CopyrightClaim",
    "DeviceRisk",
    "ModerationAction",
    "ModerationCase",
    "Report",
    "RiskEvent",
]
