# Users API

Milestone 1 implements current-user profile management, public profile privacy filtering, sessions/devices, block/unblock, data export request, and account deletion request.

All protected endpoints require:

```http
Authorization: Bearer <access_token>
```

## Current User

- `GET /users/me`
- `PATCH /users/me`

The private response includes email, verification state, preferences, and privacy settings.

## Public User

`GET /users/{user_id}`

The public response never includes private fields such as email, preferences, favorite books, or reading interests. Location and institution are hidden when the profile is private or the corresponding privacy flag is enabled.

## Sessions And Devices

- `GET /users/me/sessions`
- `DELETE /users/me/sessions/{session_id}`
- `GET /users/me/devices`

Deleting the current session immediately invalidates the current access token because access-token validation checks the backing session.

## Blocks

- `POST /users/{user_id}/block`
- `DELETE /users/{user_id}/block`

The identity permission helper denies chat initiation when either user has blocked the other. The chat module will consume this permission in Milestone 5.

## Account Requests

- `POST /users/me/delete-request`
- `POST /users/me/export-request`

These create audit and verification records. Actual export generation and account deletion completion are deferred until background jobs and retention policies are implemented.
