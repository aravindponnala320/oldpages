# ADR 0012: Moderator Role Source

## Status

Accepted

## Context

Milestone 7 needs report queues and moderator actions before OldPages has a full internal staff
identity model. The existing identity domain already has per-user preference metadata and no
separate RBAC tables.

## Decision

Use `UserPreference.metadata_json.roles` as the Milestone 7 moderator role source. The trust service
accepts `admin`, `moderator`, and `trust_moderator`.

## Consequences

This keeps trust and moderation inside the modular monolith and avoids creating premature staff
infrastructure. It is intentionally a transitional design: role assignment, scoped permissions,
staff audit views, and role-change audit events should move to dedicated staff/RBAC tables in a
later milestone.
