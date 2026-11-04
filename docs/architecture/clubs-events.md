# Clubs and Events Architecture

Milestone 9 keeps book clubs, buddy reads, readalongs, and events inside the FastAPI modular
monolith.

## Module Shape

The `oldpages_api.clubs` package owns:

- SQLAlchemy models for `book_clubs`, `club_books`, nominations, votes, milestones, buddy reads,
  readalongs, events, RSVPs, waitlists, and check-ins.
- Pydantic request/response schemas for the public REST contracts.
- A repository for query/load options and a service for ownership, visibility, voting, spoiler,
  waitlist, and calendar rules.
- Routers mounted under `/clubs`, `/club-books`, `/buddy-reads`, `/readalongs`, and `/events`.

Shared TypeScript packages expose matching response types, Zod validators, and API client methods.

## Integration Points

Community-linked clubs, readalongs, and events reuse Milestone 8 community membership checks.
Club book responses query active marketplace listings for the selected catalog book edition instead
of duplicating listing data.

Sensitive mutations write audit log rows. Full outbox-driven notifications are deferred to the
notification worker milestone.

## Behavioral Rules

Voting is deterministic and does not use randomness. Waitlist promotion is ordered by waitlist
position and only promotes entries that fit the remaining seat count. Event datetimes must include
a timezone offset, and event records also store an IANA timezone for display and calendar export.

Spoiler protection is response-level in this milestone: unread milestone prompts are returned as
`null` with `spoiler_locked=true`. Dedicated discussion-post enforcement belongs in the later
discussion and moderation milestones.

## Deferred Work

- Club membership rosters beyond owner/private visibility.
- Chapter discussion threads and announcement feeds.
- Calendar sync providers and reminder notifications.
- QR image generation; this milestone exposes a check-in code for organizer-controlled scanning.
- Group bundle purchases and marketplace purchase coordination.
