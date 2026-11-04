# Trust and Moderation

Milestone 7 keeps trust and safety inside the modular monolith.

## Storage

Trust uses these tables:

- `reports`
- `moderation_cases`
- `moderation_actions`
- `risk_events`
- `device_risk`
- `copyright_claims`

Audit entries continue to use the shared `audit_logs` table.

## Report Flow

Creating a report resolves the target, maps the report reason to severity, writes a `reports` row,
and creates a one-to-one `moderation_cases` row with an evidence snapshot. High and critical
reports create `risk_events`. Copyright reports also create `copyright_claims`.

The moderation queue orders cases by `priority_score`, then creation time. This gives high-severity
reports precedence without requiring a separate queue service.

## Moderator Access

Milestone 7 uses `UserPreference.metadata_json.roles` for local moderator authorization. Accepted
role names are `admin`, `moderator`, and `trust_moderator`. A dedicated staff/RBAC table is
deferred until there are broader internal-tool requirements.

## Evidence Access

Conversation evidence is intentionally case-bound. Moderators can read conversation evidence only
through a moderation case whose report target is a message. Each evidence access writes
`CONVERSATION_EVIDENCE_ACCESSED` to `audit_logs`.

## Enforcement

Warnings and notes keep cases in review. Dismissals close cases. Content removal suspends listings
or hides reviews. User suspension and bans set `users.status` to `suspended`, which immediately
invalidates existing access tokens and blocks future logins through the identity service.

## Deferred Work

- Staff identity and permission management
- Rule editing and rule rollout history
- Automated fraud scoring beyond the current severity-to-risk mapping
- Moderator notification workflows
- Public transparency and reputation surfaces
