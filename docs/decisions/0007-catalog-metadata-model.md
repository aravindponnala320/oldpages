# ADR 0007: Catalog Metadata Model

## Status

Accepted.

## Context

OldPages needs many listings to point to the same canonical edition. Book metadata also needs corrections, ISBN lookup, categories, academic fields, and future search indexing.

## Decision

Use a catalog module inside the modular monolith with separate tables for works, editions, authors, publishers, categories, identifiers, and academic metadata.

- `books` stores work-level metadata.
- `book_editions` stores edition-level listing targets.
- `book_identifiers` enforces global ISBN/external identifier uniqueness.
- `categories` uses an adjacency-list tree for arbitrary depth.
- ISBN lookup is a provider interface with a local provider first.

## Consequences

Listings can later reference one edition while catalog metadata stays reusable. External metadata providers can be added without changing API callers. The temporary authenticated write rule must be replaced with role-based admin permissions later.
