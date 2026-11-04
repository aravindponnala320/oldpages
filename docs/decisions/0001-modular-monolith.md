# ADR 0001: Modular Monolith

## Status

Accepted

## Context

The product blueprint requires many domains, but the implementation plan explicitly says to avoid microservices during MVP. The team needs coherent transactions, shared authorization, consistent audit logging, and low operational overhead.

## Decision

Build OldPages as a modular monolith in one repository. Runtime processes can be separate, such as API and worker, but they share the same codebase and database boundary.

## Consequences

- Domain modules can share infrastructure safely.
- Database transactions remain straightforward.
- Service extraction remains possible later only when measured scale or ownership requires it.
- Module boundaries must be enforced by code organization and reviews rather than network boundaries.
