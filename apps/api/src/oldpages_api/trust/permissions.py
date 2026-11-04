from __future__ import annotations

from oldpages_api.identity.models import User
from oldpages_api.trust.exceptions import ForbiddenTrustActionError
from oldpages_api.trust.models import ModerationCase, Report


def require_report_actor(actor: User, report: Report) -> None:
    target_user_id = report.target_user_id
    if actor.id not in {report.reporter_user_id, target_user_id}:
        raise ForbiddenTrustActionError("Only report participants can appeal this report.")


def require_case_has_message_context(case: ModerationCase) -> None:
    if case.report.target_message_id is None:
        raise ForbiddenTrustActionError(
            "Conversation evidence requires a moderation case tied to a reported message."
        )
