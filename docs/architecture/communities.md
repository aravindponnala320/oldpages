# Communities

Milestone 8 keeps communities inside the FastAPI modular monolith.

## Storage

Communities use these tables:

- `communities`
- `community_roles`
- `community_members`
- `community_rules`
- `community_channels`
- `community_posts`
- `post_comments`
- `post_reactions`
- `community_reports`

Shared audit entries continue to use `audit_logs`.

## Membership Model

Every community has roles local to that community. The creator receives the owner role, and default
owner, moderator, and member roles are seeded at creation time. A member can moderate only when
their active membership in that same community has the owner/moderator role or the `moderate`
permission.

Public communities are readable without membership. Private, secret, and institution-verified
community content requires active membership. Secret communities are excluded from discovery.

Institution-verified communities reuse `UserProfile.institution` until the later institution domain
exists. The join flow compares the profile institution to the community institution and activates
matching members immediately.

## Feed Model

Posts belong to one community and may belong to one channel. Comments and reactions are attached to
posts. Milestone 8 stores poll options as `poll_json` and returns reaction counts by aggregating
loaded reaction rows in the service response mapper.

Post approval queues, keyword filters, slow mode, bans, mutes, audit history, and moderator notes
are represented in the blueprint but are deferred until community moderation expands beyond the
Milestone 8 API.

## Marketplace Scope

The marketplace tab does not create a new listing type. It reuses existing active listings and
applies community-scope filters:

- book communities filter by `book_edition_id`
- local communities filter by `listing_locations`
- institution communities filter by seller `UserProfile.institution`

Commerce still owns offers, inventory reservation, pickup, transaction, and review behavior.

## Deferred Work

- Community search ranking and recommendation signals
- Community analytics
- Rich media rendering for photo/video post types
- Poll voting and poll close rules
- Community-specific moderation queues, bans, mutes, slow mode, keyword filters, and audit history
- Book clubs, events, reading challenges, and resource libraries
