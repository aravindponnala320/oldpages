# ADR 0013: Community-Scoped Membership and Moderation

## Status

Accepted

## Context

Milestone 8 needs community discovery, membership, feeds, and moderation boundaries without
building later staff/RBAC or institution services. Communities can be public, private, secret, or
institution verified, and moderators must not be able to act across unrelated communities.

## Decision

Use local `community_members` rows and local `community_roles` rows as the source of community
authority. A user can approve members or create pinned/announcement posts only when they are an
active member of the target community with an owner/moderator role or the `moderate` permission.

Institution-verified membership uses the existing `UserProfile.institution` field and compares it
to `communities.institution`. Dedicated institution verification records are deferred to the later
institution milestone.

## Consequences

Community permissions are explicit, queryable, and scoped to one community. This prevents global
moderator roles from leaking into community governance and keeps Milestone 8 inside the modular
monolith.

The institution check is deliberately simple. It supports early college/school communities but
should move to verified institution membership records when that domain is implemented.
