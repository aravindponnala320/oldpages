# ADR 0005: Worker Process In The Monolith

## Status

Accepted

## Context

The foundation needs a worker process for future media processing, notifications, search indexing, and event handling. The blueprint says to avoid microservices initially.

## Decision

Run the worker as a separate process from the API image using the same `oldpages_api` package.

## Consequences

- Local Compose can start API and worker independently.
- Shared configuration, database, logging, and Redis clients stay consistent.
- The worker is not a separate deployable service boundary in Milestone 0.
