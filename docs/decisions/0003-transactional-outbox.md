# ADR 0003: Transactional Outbox

## Status

Accepted

## Context

The blueprint requires reliable domain events for notifications, search indexing, moderation, payments, and other side effects. External side effects must not happen inside fragile request-only flows.

## Decision

Create an `outbox_events` table in Milestone 0. Future domain services will write domain changes and outbox rows in the same database transaction. The worker process will publish or handle those rows asynchronously.

## Consequences

- Event production can be atomic with domain state changes.
- The worker can retry failed side effects.
- Later milestones must add event type definitions, idempotent consumers, and dead-letter handling.
