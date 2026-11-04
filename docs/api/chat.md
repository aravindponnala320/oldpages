# Chat API

Milestone 5 adds authenticated buyer-seller chat for listing conversations.

## Chat Requests

- `POST /api/v1/chat-requests`
- `POST /api/v1/chat-requests/{request_id}/accept`
- `POST /api/v1/chat-requests/{request_id}/decline`
- `POST /api/v1/chat-requests/{request_id}/block`

Only authenticated users can create requests. Sellers cannot request chat on their own listings,
and blocked users cannot create requests. Accepting a request creates one conversation with the
requester and listing owner as members.

Duplicate pending or accepted requests for the same listing and user pair return the existing
request instead of creating a second thread.

## Conversations

- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}/messages`
- `POST /api/v1/conversations/{conversation_id}/messages`
- `POST /api/v1/conversations/messages/{message_id}/report`

Conversation and message reads require membership. Messages support text, image attachments from
approved user media records, and listing cards. `client_message_id` is unique per sender and
conversation so retried sends are idempotent.

Listing message responses include public listing identifiers only. Pickup details and transaction
state remain deferred to the transaction milestone.

## WebSocket

`WS /ws/conversations`

Authentication uses a bearer token in the `Authorization` header or an `access_token` query
parameter. The socket sends a `connected` event, replays messages after `last_message_id`, echoes
typing events for the authenticated user, and responds to `ping` with `pong`.

The Milestone 5 websocket is an in-process authenticated replay endpoint. Cross-process fanout is
deferred until Redis-backed realtime workers are introduced.
