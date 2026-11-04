# Reading Tracker Architecture

Milestone 10 keeps reading tracker capabilities in the `oldpages_api.reading` package inside the
FastAPI modular monolith.

## Module Shape

The reading module owns:

- SQLAlchemy models for `shelves`, `shelf_items`, `reading_progress`, `reading_notes`,
  `reading_goals`, and `reading_statistics`.
- Pydantic request and response schemas for private and public REST contracts.
- A repository for eager-loaded catalog/profile/community queries.
- A service for shelf ownership, public privacy filtering, idempotency, goal membership rules,
  statistics recomputation, and audit logging.
- Routers mounted under `/reading` and public user-scoped read endpoints under `/users`.

Shared TypeScript packages expose matching response types, Zod validators, and API client methods.

## Integration Points

Reading records point at catalog book editions. Progress updates add the book to the matching
system shelf, but they do not create listings or marketplace records.

Public shelf reads respect the existing user profile `hide_shelves` privacy flag. Community
challenge goals reuse the community active-member permission check from Milestone 8. Institution
goals use the actor profile institution instead of adding a new institution-verification subsystem.

Mutations write audit log rows. Notification fanout, public activity feeds, and challenge leaderboards
are deferred.

## Behavioral Rules

Progress updates are upserts keyed by user and book. Daily reading minutes are stored as a date-keyed
map and overwritten for the same day, which makes repeated client retries idempotent.

Notes are private by default. Public note listing never returns private notes.

Statistics are materialized snapshots, not source-of-truth counters. They can be recomputed from
`reading_progress` at any time and are upserted by user, period type, period start, and timezone.

Goal periods store explicit dates and an IANA timezone. The current milestone validates timezone
names and membership constraints but does not run scheduled goal completion jobs.

## Deferred Work

- Activity feed entries for reading updates.
- Rich highlight ranges and text-position anchors.
- Challenge leaderboards, invitations, and moderation controls.
- Scheduled goal completion and notification jobs.
- Institution verification beyond profile institution matching.
- Frontend reading tracker pages.
