# Auth API

Milestone 1 implements email/password authentication, email verification, refresh-token rotation, logout, password reset, development OAuth provider verification, and a mobile-verification placeholder.

All endpoints are under `/api/v1`.

## Register

`POST /auth/register`

Creates a user, profile, preferences, consent record, session, refresh token, and email verification record.

In `local` and `test`, the email verification token is returned in `email_verification.token` so the flow is testable before notification delivery exists. In production this field is omitted and delivery is out of band.

## Login

`POST /auth/login`

Issues a short-lived JWT access token and an opaque refresh token bound to a session. Passwords are hashed with Argon2id.

## Refresh

`POST /auth/refresh`

Rotates the refresh token. Reusing an old refresh token revokes the session and returns a `401` problem response with type:

`https://oldpages.in/problems/refresh-token-reuse`

## Logout

`POST /auth/logout`

Revokes one session using its refresh token.

## Logout All

`POST /auth/logout-all`

Requires `Authorization: Bearer <access_token>` and revokes all active sessions for the current user.

## Email Verification

`POST /auth/verify-email`

Consumes an email verification token and marks the user email as verified.

## Password Reset

`POST /auth/forgot-password` always returns `accepted: true` to avoid account enumeration.

`POST /auth/reset-password` consumes the reset token, updates the password hash, and revokes all active sessions.

## OAuth Placeholder

`POST /auth/oauth/{provider}`

Providers accepted by contract:

- `google`
- `apple`

Production verification is intentionally not configured in Milestone 1. In local/test, development tokens use:

```text
dev:<provider>:<provider_account_id>:<email>
```

Existing password accounts are not auto-linked to OAuth identities. They must be linked from an authenticated session in a later OAuth-account-management increment.

## Mobile Verification Placeholder

`POST /auth/request-mobile-verification`

Creates a mobile verification record and returns a development token outside production. SMS delivery starts in a notification-provider milestone.
