# ADR 0009: PostgreSQL Search Strategy

## Status

Accepted

## Context

OldPages needs marketplace search by title, author, ISBN, category, academic metadata, and
location. The blueprint calls for PostgreSQL full-text search first and OpenSearch later when
measured scale requires it.

## Decision

Use PostgreSQL and PostGIS for MVP search:

- Full-text indexes for listing text
- Trigram indexes for typo-tolerant matching
- JSONB indexes for listing mode filters
- PostGIS geography indexes for public radius search
- Application-level ranking over indexed candidate results

OpenSearch remains a later replacement or augmentation, not a Milestone 4 dependency.

## Consequences

This keeps local development simple and avoids an early search microservice. The tradeoff is that
ranking and autocomplete are intentionally modest until production data justifies a dedicated
search index.
