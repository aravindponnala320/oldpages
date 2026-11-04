# ADR 0014: Clubs and Events Milestone Scope

## Status

Accepted

## Context

The blueprint includes book clubs, buddy reads, readalongs, spoiler protection, events, RSVP,
waitlists, calendar export, and QR check-in. The implementation plan asks for these capabilities in
Milestone 9 without creating microservices or building later reading-tracker, payment, shipping, or
notification-provider work.

## Decision

Implement clubs and events as one modular-monolith package, `oldpages_api.clubs`, with relational
tables for durable domain records. Reuse community membership checks for community-linked records
and reuse marketplace listing responses when club books need active listing links.

Keep club participation simple in this milestone:

- Public clubs are readable and participable by authenticated users.
- Private clubs are owner-only until a dedicated club membership roster is introduced.
- Buddy-read participants and progress are stored as JSON on `buddy_reads` because the milestone
  model list does not include a separate buddy-read membership table.

Implement spoiler protection at the milestone response boundary and event check-in with organizer
codes rather than QR image generation.

## Consequences

The API supports the acceptance criteria for deterministic voting, progress-gated spoilers,
marketplace links, waitlist promotion, calendar timezone export, and organizer check-in.

The data model remains small enough for the current milestone, but later club memberships, threaded
discussions, reminders, and QR image assets should receive dedicated tables and services rather than
expanding JSON blobs indefinitely.
