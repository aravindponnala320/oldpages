# ADR 0006: Authentication Token Strategy

## Status

Accepted

## Context

The product requires short-lived access tokens, refresh-token rotation, session management, suspicious-login groundwork, and logout from all devices. Browser flows will later use secure HTTP-only cookies, while mobile clients need token-compatible APIs.

## Decision

Use short-lived signed JWT access tokens and opaque rotating refresh tokens. Access tokens include the user public ID and session public ID. Refresh tokens are stored only as HMAC-SHA256 hashes and are bound to one session.

Refresh-token reuse revokes the session and records an audit event.

## Consequences

- API/mobile clients can authenticate with bearer access tokens.
- Access-token validation can reject revoked sessions by checking the backing session row.
- Refresh-token compromise has a bounded lifetime and reuse detection.
- Web cookie transport and CSRF controls still need to be added before production browser auth.
