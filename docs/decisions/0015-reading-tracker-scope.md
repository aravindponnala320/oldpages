# ADR 0015: Reading Tracker Milestone Scope

## Status

Accepted

## Context

The blueprint includes shelves, progress, notes, highlights, goals, streaks, yearly summaries,
community challenges, and institution challenges. The implementation plan asks for these reading
tracker capabilities in Milestone 10 without building later payment, shipping, pro-seller, or
frontend application work.

## Decision

Implement reading tracker data and APIs as one modular-monolith package, `oldpages_api.reading`,
with relational tables for durable user-owned records.

Use catalog book editions as the book reference for shelves, progress, notes, and statistics. Keep
statistics materialized but recomputable from `reading_progress`, with an upsert key of user, period
type, period start, and timezone.

Make privacy conservative:

- Notes are private by default.
- Public note endpoints return only public notes.
- Public shelf endpoints honor the existing profile `hide_shelves` setting.

Implement challenge scope checks without new subsystems:

- Community goals require active membership in the selected community.
- Institution goals require the actor profile institution to match the goal metadata.
- Leaderboards, invitations, goal-completion workers, and notification fanout are deferred.

## Consequences

The milestone satisfies idempotent progress updates, private-note isolation, recomputable statistics,
timezone-aware goal periods, and challenge membership rules.

Later challenge and institution work should add dedicated tables and services for membership,
leaderboards, verification, invitations, and scheduled completion rather than overloading goal
metadata JSON.
