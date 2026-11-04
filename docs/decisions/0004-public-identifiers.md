# ADR 0004: ULID Public Identifiers

## Status

Accepted

## Context

The implementation plan requires stable public IDs and prohibits exposing sequential internal IDs. UUIDv7 or ULID are preferred.

## Decision

Use ULID-shaped 26-character public identifiers for base model mixins. Sequential database IDs can remain internal primary keys.

## Consequences

- API resources can expose sortable, non-sequential public IDs.
- Database joins keep efficient internal integer keys where appropriate.
- The current generator is dependency-free and suitable for Milestone 0. Later high-write domains should validate collision handling and database defaults.
