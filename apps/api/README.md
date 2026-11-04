# OldPages API

Milestone 0 provides the FastAPI foundation for the OldPages modular monolith. Milestone 1 adds email/password auth, session/device management, OAuth account creation hooks, and user profile APIs. Milestone 2 adds book catalog, edition, ISBN, category, author, and publisher APIs. Milestone 3 adds listing and media lifecycle APIs. Milestone 4 adds listing search, saved searches, wishlists, favorites, and follows. Milestone 5 adds buyer-seller chat and notifications. Milestone 6 adds offers, pickup sessions, transactions, and reviews. Milestone 7 adds reports, moderation cases, audited trust actions, appeals, risk records, and copyright claims. Milestone 8 adds communities, membership, feeds, reactions, reports, and scoped marketplace tabs. Milestone 9 adds clubs, buddy reads, readalongs, events, RSVP waitlists, calendar export, and organizer check-in. Milestone 10 adds reading shelves, progress, notes, goals, and recomputable statistics.

## Local Commands

From the repository root:

```sh
make setup
make up
make migrate
make test
```

From this directory after `make setup`:

```sh
../../.venv/bin/uvicorn oldpages_api.main:create_app --factory --reload
../../.venv/bin/alembic upgrade head
../../.venv/bin/pytest
```

## Endpoints

- `GET /health/live`
- `GET /health/ready`
- `GET /api/v1/foundation/example`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/logout-all`
- `POST /api/v1/auth/verify-email`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/oauth/{provider}`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/{user_id}`
- `GET /api/v1/books`
- `POST /api/v1/books`
- `POST /api/v1/books/resolve-isbn`
- `GET /api/v1/books/{book_id}`
- `PATCH /api/v1/books/{book_id}`
- `GET /api/v1/categories`
- `GET /api/v1/authors`
- `GET /api/v1/publishers`
- `POST /api/v1/listings`
- `GET /api/v1/listings/{listing_id}`
- `PATCH /api/v1/listings/{listing_id}`
- `POST /api/v1/listings/{listing_id}/publish`
- `POST /api/v1/listings/{listing_id}/pause`
- `POST /api/v1/listings/{listing_id}/relist`
- `DELETE /api/v1/listings/{listing_id}`
- `POST /api/v1/media/upload-url`
- `POST /api/v1/media/{media_id}/complete`
- `GET /api/v1/search/listings`
- `GET /api/v1/search/suggestions`
- `POST /api/v1/saved-searches`
- `GET /api/v1/saved-searches`
- `POST /api/v1/wishlists/{book_id}`
- `DELETE /api/v1/wishlists/{book_id}`
- `POST /api/v1/listings/{listing_id}/favorite`
- `DELETE /api/v1/listings/{listing_id}/favorite`
- `POST /api/v1/follows`
- `DELETE /api/v1/follows/{follow_id}`
- `POST /api/v1/chat-requests`
- `POST /api/v1/chat-requests/{request_id}/accept`
- `POST /api/v1/chat-requests/{request_id}/decline`
- `POST /api/v1/chat-requests/{request_id}/block`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}/messages`
- `POST /api/v1/conversations/{conversation_id}/messages`
- `POST /api/v1/conversations/messages/{message_id}/report`
- `WS /ws/conversations`
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{notification_id}/read`
- `GET /api/v1/notification-preferences`
- `PATCH /api/v1/notification-preferences`
- `POST /api/v1/offers`
- `POST /api/v1/offers/{offer_id}/counter`
- `POST /api/v1/offers/{offer_id}/accept`
- `POST /api/v1/offers/{offer_id}/reject`
- `POST /api/v1/offers/{offer_id}/withdraw`
- `POST /api/v1/pickups`
- `POST /api/v1/pickups/{pickup_id}/confirm`
- `POST /api/v1/transactions/{transaction_id}/complete`
- `POST /api/v1/reviews`
- `POST /api/v1/reports`
- `POST /api/v1/reports/{report_id}/appeal`
- `GET /api/v1/admin/moderation/cases`
- `GET /api/v1/admin/moderation/cases/{case_id}`
- `POST /api/v1/admin/moderation/cases/{case_id}/actions`
- `GET /api/v1/admin/moderation/cases/{case_id}/conversation-evidence`
- `GET /api/v1/admin/moderation/users/{user_id}`
- `GET /api/v1/admin/moderation/listings/{listing_id}`
- `GET /api/v1/admin/moderation/rules`
- `POST /api/v1/communities`
- `GET /api/v1/communities`
- `GET /api/v1/communities/{community_id}`
- `POST /api/v1/communities/{community_id}/join`
- `POST /api/v1/communities/{community_id}/approve-member`
- `POST /api/v1/communities/{community_id}/posts`
- `GET /api/v1/communities/{community_id}/feed`
- `GET /api/v1/communities/{community_id}/marketplace`
- `POST /api/v1/communities/{community_id}/reports`
- `POST /api/v1/posts/{post_id}/comments`
- `POST /api/v1/posts/{post_id}/reactions`
- `POST /api/v1/clubs`
- `GET /api/v1/clubs`
- `GET /api/v1/clubs/{club_id}`
- `POST /api/v1/clubs/{club_id}/books`
- `GET /api/v1/clubs/{club_id}/books`
- `POST /api/v1/clubs/{club_id}/nominations`
- `POST /api/v1/clubs/{club_id}/votes`
- `POST /api/v1/clubs/{club_id}/select-book`
- `POST /api/v1/club-books/{club_book_id}/milestones`
- `GET /api/v1/club-books/{club_book_id}/milestones`
- `POST /api/v1/buddy-reads`
- `POST /api/v1/buddy-reads/{buddy_read_id}/join`
- `POST /api/v1/buddy-reads/{buddy_read_id}/progress`
- `POST /api/v1/readalongs`
- `POST /api/v1/events`
- `GET /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `PATCH /api/v1/events/{event_id}`
- `POST /api/v1/events/{event_id}/rsvps`
- `POST /api/v1/events/{event_id}/rsvps/cancel`
- `POST /api/v1/events/{event_id}/checkins`
- `GET /api/v1/events/{event_id}/calendar.ics`
- `POST /api/v1/reading/shelves`
- `GET /api/v1/reading/shelves`
- `GET /api/v1/users/{user_id}/shelves`
- `POST /api/v1/reading/shelves/{shelf_id}/items`
- `DELETE /api/v1/reading/shelves/{shelf_id}/items/{book_id}`
- `PUT /api/v1/reading/progress/{book_id}`
- `GET /api/v1/reading/progress`
- `POST /api/v1/reading/notes`
- `GET /api/v1/reading/notes`
- `GET /api/v1/users/{user_id}/reading-notes`
- `POST /api/v1/reading/goals`
- `GET /api/v1/reading/goals`
- `POST /api/v1/reading/statistics/recompute`
- `GET /api/v1/reading/statistics`

Readiness checks PostgreSQL and Redis. The example endpoint exists only to verify the API contract and request middleware in CI. See `docs/api/auth.md`, `docs/api/users.md`, `docs/api/catalog.md`, `docs/api/listings.md`, `docs/api/search.md`, `docs/api/chat.md`, `docs/api/notifications.md`, `docs/api/commerce.md`, `docs/api/trust.md`, `docs/api/communities.md`, `docs/api/clubs-events.md`, `docs/api/reading.md`, `docs/api/payments-orders-shipping.md`, `docs/api/business-subscriptions.md`, `docs/api/institutions-donations.md`, and `docs/api/recommendations.md` for API behavior.
