# ADR 0011: Inventory Reservation

## Status

Accepted

## Context

OldPages needs structured offers that can reserve scarce peer-to-peer inventory. The blueprint
requires that two buyers cannot reserve the same last copy.

## Decision

Reserve inventory during offer acceptance with a single conditional database update against
`listing_inventory`. The update decrements available quantity only when enough quantity remains.
The transaction row and offer status update are committed with that inventory change.

## Consequences

This keeps reservation logic inside PostgreSQL and the modular monolith. The tradeoff is that
reservation expiration, payment authorization, and inventory release workflows remain later
milestone work.
