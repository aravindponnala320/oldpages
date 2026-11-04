# ADR 0002: PostgreSQL With PostGIS

## Status

Accepted

## Context

OldPages requires location-aware discovery while preserving exact-location privacy. The blueprint also calls for relational constraints and later full-text search.

## Decision

Use PostgreSQL as the primary database and install PostGIS from the first migration.

## Consequences

- Radius search and approximate-location features can be implemented without changing databases.
- Relational constraints can protect marketplace invariants.
- Local development uses the `postgis/postgis` Docker image.
- Search begins with PostgreSQL capabilities before considering OpenSearch.
