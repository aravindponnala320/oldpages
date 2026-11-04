# Identity And Profiles

Milestone 1 adds the identity and user-profile foundation.

## Tables

- `users`
- `user_profiles`
- `user_sessions`
- `user_devices`
- `social_accounts`
- `user_verifications`
- `user_preferences`
- `user_blocks`
- `consent_records`
- `audit_logs`

All public API identifiers use ULID-style `public_id` values. Internal integer IDs remain private.

## Auth Tokens

Access tokens are signed JWTs with a short expiry. They include:

- `sub`: user public ID
- `session_id`: session public ID
- `token_type`: `access`
- `iat`
- `exp`

Refresh tokens are opaque values in the format:

```text
<session_public_id>.<secret>
```

Only an HMAC-SHA256 hash of the full refresh token is stored. Refresh rotates the token in place. Reusing an older token marks the session as revoked with `refresh_reuse`.

## Passwords

Passwords are hashed with Argon2id through `argon2-cffi`.

## Verification Tokens

Email verification, mobile verification, password reset, data export, and account deletion requests use one-time opaque tokens stored only as HMAC-SHA256 hashes.

Development and test environments expose these tokens in responses until notification delivery exists. Production responses are out of band.

## OAuth

The OAuth verifier is a provider abstraction. Milestone 1 includes local/test development-token verification for Google and Apple-ready contracts, but no production provider network calls.

Existing password accounts are not auto-linked to OAuth identities. This prevents account takeover through untrusted provider payloads.

## Privacy

Private profile responses are available only to the authenticated owner. Public profile responses filter:

- email
- preferences
- favorite books/authors/genres
- reading interests
- location when hidden or non-public
- institution when hidden or non-public
