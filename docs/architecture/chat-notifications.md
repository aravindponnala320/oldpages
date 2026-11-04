# Chat and Notifications

Milestone 5 keeps chat and notifications inside the FastAPI modular monolith.

## Storage

Chat uses these tables:

- `chat_requests`
- `conversations`
- `conversation_members`
- `messages`
- `message_attachments`
- `message_reads`
- `message_reports`

Notifications use these tables:

- `notifications`
- `notification_preferences`
- `notification_deliveries`

All public API identifiers remain ULIDs. Internal integer keys stay private.

## Access Control

Chat request recipients can accept, decline, or block requests. Conversation and message reads
require an active, muted, or archived membership. A user block between the requester and seller
prevents new chat requests and accepted conversations.

Message sends persist before the API returns an acknowledgement. The unique
`conversation_id`, `sender_user_id`, and `client_message_id` constraint makes client retries
idempotent.

## Realtime

`/ws/conversations` authenticates with existing access tokens and replays recent messages after
the provided `last_message_id`. The in-process socket path is enough for local development and CI.
Redis fanout, presence storage, and multi-instance delivery are deferred until production scale
requires them.

## Notification Delivery

Domain services create notification rows and durable `notification_deliveries` rows in the same
database transaction as the chat event. The async delivery hook is intentionally a placeholder in
Milestone 5; later workers can claim pending rows and send email or push without changing chat
transaction boundaries.

## Reports

Message reports are recorded once per reporter and message. Moderation queues and enforcement
actions belong to the moderation milestone.
