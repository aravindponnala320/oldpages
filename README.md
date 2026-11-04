# OldPages.in

OldPages.in is being built as a modular monolith for a trusted book marketplace and reader community. This repository contains the Milestone 0 foundation through the Milestone 14 recommendation layer: local infrastructure, API shell, web/admin shells, shared TypeScript packages, migrations, CI, auth/profile APIs, catalog APIs, listing APIs, media upload records, search APIs, user collection APIs, chat APIs, notification APIs, offer APIs, transaction APIs, review APIs, report APIs, moderation APIs, community APIs, club APIs, event APIs, reading shelf/progress/note/goal/statistic APIs, cart/order/payment/shipping/dispute APIs, professional seller APIs, subscription/promotion/coupon APIs, institution/donation APIs, rule-based recommendation APIs, and test harnesses.

The product blueprint and milestone plan live in:

- `docs/OLDPAGES_MASTER_BLUEPRINT.md`
- `docs/CODEX_IMPLEMENTATION_PLAN.md`

## Repository Layout

```text
apps/
  api/      FastAPI application, Alembic migrations, worker entrypoint
  web/      Next.js public web shell
  admin/    Next.js admin shell
packages/
  api-client/
  config/
  design-tokens/
  shared-types/
  validation/
infrastructure/docker/
docs/
scripts/
```

## Local Development

Copy the environment template when you need local overrides:

```sh
cp .env.example .env
```

Install local toolchains:

```sh
make setup
```

Start the full local stack:

```sh
make up
```

Apply database migrations:

```sh
make migrate
```

Run checks:

```sh
make lint
make typecheck
make test
make e2e
```

Export the OpenAPI document:

```sh
make api-docs
```

Stop local services:

```sh
make down
```

## Service URLs

- API: `http://localhost:8000`
- API live health: `http://localhost:8000/health/live`
- API readiness: `http://localhost:8000/health/ready`
- Public web shell: `http://localhost:3000`
- Admin shell: `http://localhost:3001`
- MinIO console: `http://localhost:9001`

## Implemented Scope

Implemented:

- FastAPI application factory
- Configuration module
- Async SQLAlchemy database setup
- Redis client setup
- Request ID middleware
- Structured JSON logging
- RFC 7807-style error responses
- OpenTelemetry FastAPI instrumentation hook
- Health endpoints
- Alembic migration for PostGIS and the transactional outbox table
- Worker process entrypoint using the same API codebase
- Next.js web and admin shells
- Shared TypeScript packages
- Docker Compose for PostgreSQL/PostGIS, Redis, MinIO, API, worker, web, and admin
- GitHub Actions CI for backend, frontend, Docker, secret scanning, and container scanning
- Email/password identity foundation
- User profiles and public privacy filtering
- Session, device, refresh-token rotation, and logout flows
- Verification/reset token records
- OAuth provider abstraction with local/test development verifier
- User block permissions for later chat enforcement
- Book catalog work and edition records
- Authors, publishers, ISBN/external identifiers, and category tree
- Academic metadata for course, exam, grade, and institution use cases
- ISBN lookup provider abstraction with local catalog resolution
- Authenticated manual catalog entry and metadata correction hooks
- Draft listing creation from catalog book ID or ISBN
- Listing condition, location, delivery, inventory, image, and price-history records
- Listing publish, pause, relist, and soft-delete transitions
- Direct-to-storage media upload record flow with processing placeholders
- Public listing responses that hide exact pickup coordinates and private notes
- PostgreSQL-backed listing search with full-text, trigram, and PostGIS index support
- Search suggestions, zero-result logging, saved searches, wishlist items, listing favorites, and follows
- Public search responses that expose approximate location only
- Buyer-seller chat requests, accepted listing conversations, message persistence, image attachment references, read receipts, reports, and websocket replay
- In-app notification inbox, notification preferences, and durable pending email/push delivery rows
- Structured offers, counteroffers, pickup sessions, handover-code completion, atomic inventory reservation, and transaction-linked reviews
- User/listing/message/review/copyright reports, moderation cases, audited actions, appeals, risk events, device risk records, and copyright claims
- Admin moderation endpoints for queues, case detail, user/listing detail, conversation evidence access, rules, and action history
- Community creation, discovery, scoped membership, owner/moderator roles, feeds, posts, comments, reactions, reports, and marketplace tabs
- Book clubs, club books, nominations, deterministic ranked voting, progress-gated milestones, buddy reads, readalongs, events, RSVP capacity/waitlist handling, calendar export, and organizer check-in
- Reading shelves, shelf items, idempotent progress updates, private/public notes, reading goals, community/institution challenge constraints, and recomputable reading statistics
- Seller-specific carts, checkout orders, local payment initiation, payment/shipping webhook state transitions, refunds, capped payouts, shipments, shipment status updates, and disputes
- Business profiles, business locations, scoped staff records, idempotent inventory import tracking with failed-row CSV reports, subscriptions, centralized entitlements, paid promotion orders, and coupon validation/admin management
- Institution profiles, admin-scoped verification, domain verification, membership, donation campaigns, accepted-condition pledge rules, recipient confirmation, public impact summaries, and receipts
- Rule-based recommendations, category/price/condition suggestions, editable listing-description assistance, review-only fraud prioritization, similar listings, recommendation metadata, dismiss/click tracking, and feedback

Not implemented yet:

- Production email/push notification providers, Redis websocket fanout, and production-scale realtime load testing
- External payment capture/refund/payout providers, external shipping labels, and reservation expiration workers
- Dedicated staff RBAC tables and editable moderation rule rollout history
- Full CSV file upload parsing, bulk edit, analytics dashboards, and production subscription billing providers
- Persisted user-correction workflows for recommendation assistance
- Community analytics, poll voting, rich community moderation, club rosters, discussion threads, event reminders, challenge leaderboards, and scheduled goal completion
- Production deployment infrastructure
