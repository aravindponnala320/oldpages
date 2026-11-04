from __future__ import annotations

from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.listings.tasks import refresh_listing_search_document
from oldpages_api.trust.events import (
    CONVERSATION_EVIDENCE_ACCESSED,
    COPYRIGHT_CLAIM_CREATED,
    MODERATION_ACTION_TAKEN,
    MODERATION_APPEAL_SUBMITTED,
    REPORT_CREATED,
    RISK_EVENT_CREATED,
)
from oldpages_api.trust.exceptions import (
    ForbiddenTrustActionError,
    InvalidTrustStateTransitionError,
    ModerationCaseNotFoundError,
    ReportNotFoundError,
    TrustValidationError,
)
from oldpages_api.trust.models import (
    CopyrightClaim,
    DeviceRisk,
    ModerationAction,
    ModerationCase,
    Report,
    RiskEvent,
)
from oldpages_api.trust.permissions import require_case_has_message_context, require_report_actor
from oldpages_api.trust.repository import TrustRepository
from oldpages_api.trust.schemas import (
    ConversationEvidenceMessage,
    ConversationEvidenceResponse,
    CopyrightClaimResponse,
    DeviceRiskResponse,
    ModerationActionRequest,
    ModerationActionResponse,
    ModerationCaseListResponse,
    ModerationCaseResponse,
    ModerationListingResponse,
    ModerationRuleConfigResponse,
    ModerationUserResponse,
    ReportAppealRequest,
    ReportCreateRequest,
    ReportResponse,
    ReportSeverity,
    ReportStatus,
    ReportTargetType,
    RiskEventResponse,
    TargetSummary,
    TrustUserSummary,
)

MODERATOR_ROLES = ["admin", "moderator", "trust_moderator"]
SEVERITY_BY_REASON: dict[str, ReportSeverity] = {
    "child_safety": "critical",
    "payment_fraud": "critical",
    "copyright_infringement": "high",
    "dangerous_meetup": "high",
    "hate_speech": "high",
    "personal_information": "high",
    "scam": "high",
    "sexual_content": "high",
    "counterfeit": "medium",
    "fake_listing": "medium",
    "fake_review": "medium",
    "misleading_condition": "medium",
    "piracy": "medium",
    "stolen_image": "medium",
    "harassment": "medium",
    "spam": "low",
    "other": "low",
}
SEVERITY_SCORE = {"low": 20, "medium": 50, "high": 80, "critical": 100}


class TrustService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TrustRepository(session)

    async def create_report(
        self,
        payload: ReportCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReportResponse:
        target = await self.resolve_target(payload)
        severity = SEVERITY_BY_REASON[payload.reason]
        evidence = dict(payload.evidence)
        if payload.device_fingerprint:
            evidence["device_fingerprint"] = payload.device_fingerprint
        report = Report(
            description=payload.description,
            evidence_json=evidence,
            reason=payload.reason,
            reporter_user_id=actor.id,
            severity=severity,
            status="open",
            target_listing_id=target.listing_id,
            target_message_id=target.message_id,
            target_review_id=target.review_id,
            target_type=payload.target_type,
            target_user_id=target.user_id,
        )
        self.repo.add(report)
        await self.repo.flush()
        case = ModerationCase(
            evidence_snapshot_json=report_evidence_snapshot(report, target.public_id),
            priority_score=priority_for_report(report),
            report_id=report.id,
            severity=severity,
            status="open",
            summary=case_summary(payload, target.public_id),
        )
        self.repo.add(case)
        await self.repo.flush()
        if severity in {"high", "critical"}:
            await self.add_risk_event(report, target.user_id, payload.reason, severity)
        if payload.device_fingerprint:
            await self.upsert_device_risk(
                payload.device_fingerprint,
                target.user_id,
                severity,
                payload.reason,
            )
        if payload.reason == "copyright_infringement" and payload.copyright_claim is not None:
            self.repo.add(
                CopyrightClaim(
                    claimant_email=payload.copyright_claim.claimant_email,
                    claimant_statement=payload.copyright_claim.claimant_statement,
                    evidence_json=evidence,
                    report_id=report.id,
                    status="submitted",
                    work_title=payload.copyright_claim.work_title,
                )
            )
            await self.audit(
                action=COPYRIGHT_CLAIM_CREATED,
                actor_user_id=actor.id,
                context=context,
                payload={"report_id": report.public_id},
                target_user_id=target.user_id,
            )
        await self.audit(
            action=REPORT_CREATED,
            actor_user_id=actor.id,
            context=context,
            payload={"report_id": report.public_id, "severity": severity},
            target_user_id=target.user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_report_model(report.public_id)
        return report_response(reloaded)

    async def appeal_report(
        self,
        report_id: str,
        payload: ReportAppealRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReportResponse:
        report = await self.get_report_model(report_id)
        require_report_actor(actor, report)
        if report.case is None:
            raise InvalidTrustStateTransitionError("Report has no moderation case to appeal.")
        report.status = "appealed"
        report.case.status = "appealed"
        self.repo.add(
            ModerationAction(
                action_type="appeal_submitted",
                actor_user_id=actor.id,
                case_id=report.case.id,
                evidence_snapshot_json=report.case.evidence_snapshot_json,
                metadata_json={"appeal_statement": payload.statement},
                moderator_user_id=None,
                reason=payload.statement,
            )
        )
        await self.audit(
            action=MODERATION_APPEAL_SUBMITTED,
            actor_user_id=actor.id,
            context=context,
            payload={"case_id": report.case.public_id, "report_id": report.public_id},
            target_user_id=report.target_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_report_model(report.public_id)
        return report_response(reloaded)

    async def list_cases(
        self,
        actor: User,
        *,
        cursor: str | None,
        limit: int,
        status: str | None,
    ) -> ModerationCaseListResponse:
        await self.require_moderator(actor)
        cases, next_cursor = await self.repo.list_cases(
            cursor=cursor,
            limit=limit,
            status=status,
        )
        return ModerationCaseListResponse(
            items=[case_response(case) for case in cases],
            next_cursor=next_cursor,
        )

    async def get_case(self, case_id: str, actor: User) -> ModerationCaseResponse:
        await self.require_moderator(actor)
        case = await self.get_case_model(case_id)
        return case_response(case)

    async def take_action(
        self,
        case_id: str,
        payload: ModerationActionRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ModerationCaseResponse:
        await self.require_moderator(actor)
        case = await self.get_case_model(case_id)
        target_user = case_target_user(case)
        action = ModerationAction(
            action_type=payload.action_type,
            actor_user_id=actor.id,
            case_id=case.id,
            duration_until=payload.duration_until,
            evidence_snapshot_json=case.evidence_snapshot_json,
            metadata_json=payload.metadata,
            moderator_user_id=actor.id,
            reason=payload.reason,
        )
        self.repo.add(action)
        case.assigned_moderator_user_id = actor.id
        await self.apply_action(case, payload.action_type, target_user)
        await self.audit(
            action=MODERATION_ACTION_TAKEN,
            actor_user_id=actor.id,
            context=context,
            payload={"action_type": payload.action_type, "case_id": case.public_id},
            target_user_id=target_user.id if target_user else None,
        )
        await self.repo.commit()
        reloaded = await self.get_case_model(case.public_id)
        return case_response(reloaded)

    async def conversation_evidence(
        self,
        case_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ConversationEvidenceResponse:
        await self.require_moderator(actor)
        case = await self.get_case_model(case_id)
        require_case_has_message_context(case)
        message = case.report.target_message
        if message is None:
            raise InvalidTrustStateTransitionError("Reported message is no longer available.")
        reloaded = await self.repo.get_message_by_public_id(message.public_id)
        if reloaded is None:
            raise InvalidTrustStateTransitionError("Reported message is no longer available.")
        await self.audit(
            action=CONVERSATION_EVIDENCE_ACCESSED,
            actor_user_id=actor.id,
            context=context,
            payload={"case_id": case.public_id, "message_id": reloaded.public_id},
            target_user_id=case.report.target_user_id,
        )
        await self.repo.commit()
        messages = sorted(
            reloaded.conversation.messages, key=lambda item: (item.created_at, item.id)
        )
        return ConversationEvidenceResponse(
            case_id=case.public_id,
            conversation_id=reloaded.conversation.public_id,
            messages=[
                ConversationEvidenceMessage(
                    body=item.body,
                    created_at=item.created_at,
                    id=item.public_id,
                    message_type=item.message_type,
                    sender_user_id=item.sender.public_id,
                )
                for item in messages[-25:]
            ],
            report_id=case.report.public_id,
        )

    async def moderation_user(self, user_id: str, actor: User) -> ModerationUserResponse:
        await self.require_moderator(actor)
        user = await self.repo.get_user_by_public_id(user_id)
        if user is None:
            raise TrustValidationError("User not found.")
        return ModerationUserResponse(
            email=user.email,
            id=user.public_id,
            report_count=await self.repo.report_count_for_user(user.id),
            status=user.status,
        )

    async def moderation_listing(self, listing_id: str, actor: User) -> ModerationListingResponse:
        await self.require_moderator(actor)
        listing = await self.repo.get_listing_by_public_id(listing_id)
        if listing is None:
            raise TrustValidationError("Listing not found.")
        return ModerationListingResponse(
            id=listing.public_id,
            report_count=await self.repo.report_count_for_listing(listing.id),
            seller_user_id=listing.seller.public_id,
            status=listing.status,
            title=listing.title_snapshot,
        )

    async def rules(self, actor: User) -> ModerationRuleConfigResponse:
        await self.require_moderator(actor)
        return ModerationRuleConfigResponse(
            action_types=["warn", "remove_content", "suspend", "ban", "dismiss", "restore", "note"],
            moderator_roles=MODERATOR_ROLES,
            severity_by_reason=SEVERITY_BY_REASON,
        )

    async def require_moderator(self, actor: User) -> None:
        for role in MODERATOR_ROLES:
            if await self.repo.user_has_role(actor.id, role):
                return
        raise ForbiddenTrustActionError("Moderator role is required.")

    async def resolve_target(self, payload: ReportCreateRequest) -> ReportTarget:
        if payload.target_type == "user":
            user = await self.repo.get_user_by_public_id(cast("str", payload.target_id))
            if user is None:
                raise TrustValidationError("Reported user not found.")
            return ReportTarget(user_id=user.id, public_id=user.public_id)
        if payload.target_type == "listing":
            listing = await self.repo.get_listing_by_public_id(cast("str", payload.target_id))
            if listing is None:
                raise TrustValidationError("Reported listing not found.")
            return ReportTarget(
                listing_id=listing.id,
                public_id=listing.public_id,
                user_id=listing.seller_user_id,
            )
        if payload.target_type == "message":
            message = await self.repo.get_message_by_public_id(cast("str", payload.target_id))
            if message is None:
                raise TrustValidationError("Reported message not found.")
            return ReportTarget(
                message_id=message.id,
                public_id=message.public_id,
                user_id=message.sender_user_id,
            )
        if payload.target_type == "review":
            review = await self.repo.get_review_by_public_id(cast("str", payload.target_id))
            if review is None:
                raise TrustValidationError("Reported review not found.")
            return ReportTarget(
                review_id=review.id,
                public_id=review.public_id,
                user_id=review.reviewer_user_id,
            )
        return ReportTarget(public_id=payload.target_id)

    async def add_risk_event(
        self,
        report: Report,
        user_id: int | None,
        reason: str,
        severity: str,
    ) -> None:
        self.repo.add(
            RiskEvent(
                event_type=f"report:{reason}",
                metadata_json={"report_id": report.public_id},
                report_id=report.id,
                score=SEVERITY_SCORE[severity],
                severity=severity,
                status="open",
                user_id=user_id,
            )
        )
        self.repo.add(
            AuditLog(
                action=RISK_EVENT_CREATED,
                actor_user_id=None,
                context_json={"report_id": report.public_id, "severity": severity},
                target_user_id=user_id,
            )
        )

    async def upsert_device_risk(
        self,
        fingerprint: str,
        user_id: int | None,
        severity: str,
        reason: str,
    ) -> None:
        risk = await self.repo.get_device_risk_by_fingerprint(fingerprint)
        score = SEVERITY_SCORE[severity]
        risk_level = "blocked" if severity == "critical" else severity
        if risk is None:
            self.repo.add(
                DeviceRisk(
                    device_fingerprint=fingerprint,
                    last_seen_at=utc_now(),
                    reasons_json=[reason],
                    risk_level=risk_level,
                    score=score,
                    user_id=user_id,
                )
            )
            return
        previous_score = risk.score
        risk.last_seen_at = utc_now()
        risk.score = max(risk.score, score)
        if score >= previous_score:
            risk.risk_level = risk_level
        if reason not in risk.reasons_json:
            risk.reasons_json = [*risk.reasons_json, reason]
        if user_id is not None:
            risk.user_id = user_id

    async def apply_action(
        self,
        case: ModerationCase,
        action_type: str,
        target_user: User | None,
    ) -> None:
        if action_type in {"warn", "note"}:
            case.status = "in_review"
            case.report.status = "in_review"
            return
        if action_type == "dismiss":
            case.status = "closed"
            case.closed_at = utc_now()
            case.report.status = "dismissed"
            return
        if action_type == "restore":
            if target_user is not None and target_user.status == "suspended":
                target_user.status = "active"
            if (
                case.report.target_listing is not None
                and case.report.target_listing.status == "suspended"
            ):
                case.report.target_listing.status = "active"
                await refresh_listing_search_document(case.report.target_listing.id)
            case.status = "actioned"
            case.report.status = "resolved"
            return
        if action_type in {"suspend", "ban"}:
            if target_user is None:
                raise InvalidTrustStateTransitionError("This case has no target user to suspend.")
            target_user.status = "suspended"
        if action_type == "remove_content" and case.report.target_listing is not None:
            case.report.target_listing.status = "suspended"
            await refresh_listing_search_document(case.report.target_listing.id)
        if action_type == "remove_content" and case.report.target_review is not None:
            case.report.target_review.status = "hidden"
        case.status = "actioned"
        case.report.status = "resolved"

    async def get_report_model(self, report_id: str) -> Report:
        report = await self.repo.get_report_by_public_id(report_id)
        if report is None:
            raise ReportNotFoundError()
        return report

    async def get_case_model(self, case_id: str) -> ModerationCase:
        case = await self.repo.get_case_by_public_id(case_id)
        if case is None:
            raise ModerationCaseNotFoundError()
        report = await self.repo.get_report_by_id(case.report_id)
        if report is not None:
            report.case = case
            case.report = report
        await case.awaitable_attrs.actions
        await case.awaitable_attrs.assigned_moderator
        return case

    async def audit(
        self,
        *,
        action: str,
        actor_user_id: int | None,
        context: AuthenticatedRequestContext,
        payload: dict[str, str],
        target_user_id: int | None,
    ) -> None:
        self.repo.add(
            AuditLog(
                action=action,
                actor_user_id=actor_user_id,
                context_json=payload,
                ip_address=context.ip_address,
                target_user_id=target_user_id,
                user_agent=context.user_agent,
            )
        )


class ReportTarget:
    def __init__(
        self,
        *,
        listing_id: int | None = None,
        message_id: int | None = None,
        public_id: str | None,
        review_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        self.listing_id = listing_id
        self.message_id = message_id
        self.public_id = public_id
        self.review_id = review_id
        self.user_id = user_id


def case_target_user(case: ModerationCase) -> User | None:
    if case.report.target_user is not None:
        return case.report.target_user
    if case.report.target_listing is not None:
        return case.report.target_listing.seller
    if case.report.target_message is not None:
        return case.report.target_message.sender
    if case.report.target_review is not None:
        return case.report.target_review.reviewer
    return None


def priority_for_report(report: Report) -> int:
    score = SEVERITY_SCORE[report.severity]
    if report.reason in {"child_safety", "payment_fraud", "dangerous_meetup"}:
        score += 10
    if report.target_type == "message":
        score += 5
    return min(score, 100)


def report_evidence_snapshot(report: Report, target_public_id: str | None) -> dict[str, Any]:
    return {
        "description": report.description,
        "evidence": report.evidence_json,
        "reason": report.reason,
        "reported_at": report.created_at.isoformat() if report.created_at else None,
        "target_id": target_public_id,
        "target_type": report.target_type,
    }


def case_summary(payload: ReportCreateRequest, target_public_id: str | None) -> str:
    target = target_public_id or "unlinked target"
    return f"{payload.reason} report on {payload.target_type} {target}"


def target_summary(report: Report) -> TargetSummary:
    target_id = None
    if report.target_user is not None:
        target_id = report.target_user.public_id
    elif report.target_listing is not None:
        target_id = report.target_listing.public_id
    elif report.target_message is not None:
        target_id = report.target_message.public_id
    elif report.target_review is not None:
        target_id = report.target_review.public_id
    return TargetSummary(id=target_id, type=cast("ReportTargetType", report.target_type))


def report_response(report: Report) -> ReportResponse:
    return ReportResponse(
        case_id=report.case.public_id if report.case else None,
        created_at=report.created_at,
        description=report.description,
        evidence=report.evidence_json,
        id=report.public_id,
        reason=report.reason,
        reporter=TrustUserSummary(id=report.reporter.public_id),
        severity=cast("ReportSeverity", report.severity),
        status=cast("ReportStatus", report.status),
        target=target_summary(report),
    )


def action_response(action: ModerationAction) -> ModerationActionResponse:
    return ModerationActionResponse(
        action_type=cast(Any, action.action_type),
        actor_user_id=action.actor.public_id if action.actor else None,
        created_at=action.created_at,
        duration_until=action.duration_until,
        evidence_snapshot=action.evidence_snapshot_json,
        id=action.public_id,
        metadata=action.metadata_json,
        moderator_user_id=action.moderator.public_id if action.moderator else None,
        reason=action.reason,
    )


def case_response(case: ModerationCase) -> ModerationCaseResponse:
    return ModerationCaseResponse(
        actions=[
            action_response(action)
            for action in sorted(case.actions, key=lambda item: item.created_at)
        ],
        assigned_moderator_user_id=case.assigned_moderator.public_id
        if case.assigned_moderator
        else None,
        created_at=case.created_at,
        evidence_snapshot=case.evidence_snapshot_json,
        id=case.public_id,
        priority_score=case.priority_score,
        report=report_response(case.report),
        severity=cast("ReportSeverity", case.severity),
        status=cast(Any, case.status),
        summary=case.summary,
    )


def risk_event_response(event: RiskEvent) -> RiskEventResponse:
    return RiskEventResponse(
        created_at=event.created_at,
        event_type=event.event_type,
        id=event.public_id,
        score=event.score,
        severity=cast("ReportSeverity", event.severity),
        status=cast(Any, event.status),
        user_id=event.user.public_id if event.user else None,
    )


def device_risk_response(risk: DeviceRisk) -> DeviceRiskResponse:
    return DeviceRiskResponse(
        device_fingerprint=risk.device_fingerprint,
        id=risk.public_id,
        reasons=risk.reasons_json,
        risk_level=cast(Any, risk.risk_level),
        score=risk.score,
        user_id=risk.user.public_id if risk.user else None,
    )


def copyright_claim_response(claim: CopyrightClaim) -> CopyrightClaimResponse:
    return CopyrightClaimResponse(
        claimant_email=claim.claimant_email,
        created_at=claim.created_at,
        id=claim.public_id,
        report_id=claim.report.public_id if claim.report else None,
        status=cast(Any, claim.status),
        work_title=claim.work_title,
    )
