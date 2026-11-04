# Notifications API

Milestone 5 adds the authenticated notification inbox and user delivery preferences.

## Inbox

- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{notification_id}/read`

Notifications are scoped to the authenticated user and are cursor paginated. Chat request,
acceptance, decline, and message events create unread in-app notifications plus pending delivery
rows for enabled channels.

## Preferences

- `GET /api/v1/notification-preferences`
- `PATCH /api/v1/notification-preferences`

Preferences control in-app, email, and push channels as well as chat request, message, and
marketing categories. Email and push providers are represented by durable pending delivery rows in
Milestone 5; real provider integrations are intentionally deferred.

Quiet hours accept `HH:MM` 24-hour values.
