# ADR 0010: WebSocket Architecture

## Status

Accepted

## Context

OldPages needs near-real-time conversation updates, typing indicators, and reconnect recovery. The
blueprint calls for a modular monolith first and avoids early microservices.

## Decision

Implement Milestone 5 realtime chat as an authenticated FastAPI WebSocket endpoint inside the API
process:

- Existing access tokens authenticate socket connections.
- Clients can pass `last_message_id` to replay missed messages on reconnect.
- Message writes remain HTTP transactions that persist before acknowledgement.
- Notification delivery is represented by durable database rows, not socket state.

## Consequences

This keeps the local stack and CI simple. The tradeoff is that cross-process broadcast, presence,
and push delivery are placeholders until Redis-backed fanout and worker delivery are added.
