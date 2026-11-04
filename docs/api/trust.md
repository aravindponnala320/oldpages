# Trust and Moderation API

Milestone 7 adds user reports, moderation cases, audited actions, appeals, basic risk records, and
copyright claim intake.

## Reports

- `POST /api/v1/reports`
- `POST /api/v1/reports/{report_id}/appeal`

Authenticated users can report users, listings, messages, reviews, or copyright issues. Reports
capture the reporter, target, reason, severity, description, and evidence JSON. Copyright reports
require a `copyright_claim` payload.

Reasons are mapped to low, medium, high, or critical severity in the trust service. High and
critical reports create risk events. Device fingerprints supplied with reports update the
`device_risk` table.

Report appeals can be submitted by the reporter or the reported user. Appeal actions store the
original moderation case evidence snapshot before later review.

## Admin Moderation

- `GET /api/v1/admin/moderation/cases`
- `GET /api/v1/admin/moderation/cases/{case_id}`
- `POST /api/v1/admin/moderation/cases/{case_id}/actions`
- `GET /api/v1/admin/moderation/cases/{case_id}/conversation-evidence`
- `GET /api/v1/admin/moderation/users/{user_id}`
- `GET /api/v1/admin/moderation/listings/{listing_id}`
- `GET /api/v1/admin/moderation/rules`

Admin moderation endpoints require a moderator role. In Milestone 7, roles are read from
`UserPreference.metadata_json.roles`.

Case queues sort high-priority reports first. Actions include warning, content removal,
suspension, ban, dismissal, restore, and note. Every moderator action writes an audit log entry.

Conversation evidence access is available only when the moderation case is tied to a reported
message. Evidence access writes an audit log entry and returns the last 25 messages in the
conversation.

Suspensions set the target user status to `suspended`; existing and future authenticated requests
then fail identity token validation because active user status is required.
