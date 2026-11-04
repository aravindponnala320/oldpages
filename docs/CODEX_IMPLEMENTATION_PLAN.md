# OldPages.in — Codex Implementation Plan

This document is written for Codex or another coding agent. Follow it in order. Do not attempt to generate the full application in one step.

---

## 1. Operating Instructions for Codex

1. Read `OLDPAGES_MASTER_BLUEPRINT.md` before changing code.
2. Build a modular monolith.
3. Keep web, mobile, backend, and shared contracts in one monorepo.
4. Never add a feature without:
   - Schema
   - Service logic
   - Authorization
   - Tests
   - Documentation
5. Do not create microservices during MVP.
6. Do not silently change database models.
7. Generate Alembic migrations for every schema change.
8. Use typed API contracts.
9. Add idempotency for all payment, order, webhook, import, and notification side effects.
10. Ask for a decision only when a missing business rule blocks correctness. Otherwise choose a safe default and document it.
11. Complete one milestone at a time.
12. At the end of each milestone:
   - Run tests
   - Run lint
   - Run type checks
   - Update documentation
   - Produce a summary of files changed
   - List remaining risks

---

## 2. Monorepo Structure

```text
oldpages/
  apps/
    web/
    mobile/
    admin/
    api/
    worker/
  packages/
    api-client/
    shared-types/
    validation/
    design-tokens/
    config/
  infrastructure/
    docker/
    terraform/
  docs/
    architecture/
    api/
    decisions/
  scripts/
  .github/
```

Recommended tooling:

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy 2.x async
- Alembic
- Pydantic v2
- PostgreSQL
- PostGIS
- Redis
- Pytest
- Ruff
- Mypy
- HTTPX
- Factory Boy or equivalent

### Web
- Next.js
- TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form
- Zod
- Playwright
- Vitest

### Mobile
- Expo React Native
- TypeScript
- Expo Router
- TanStack Query
- Zustand
- SecureStore

### DevOps
- Docker Compose locally
- GitHub Actions
- Managed PostgreSQL in production
- Managed Redis
- S3-compatible storage

---

## 3. Backend Module Template

Every module should follow:

```text
module_name/
  __init__.py
  router.py
  schemas.py
  models.py
  service.py
  repository.py
  permissions.py
  exceptions.py
  events.py
  tasks.py
  tests/
```

Responsibilities:

- `router.py`: HTTP transport only
- `schemas.py`: request/response models
- `models.py`: SQLAlchemy models
- `service.py`: business logic
- `repository.py`: persistence
- `permissions.py`: authorization
- `exceptions.py`: domain errors
- `events.py`: event types
- `tasks.py`: background work

---

## 4. Global Engineering Conventions

### API
- Prefix: `/api/v1`
- JSON only, except uploads
- RFC 7807-style error responses
- Cursor pagination for feeds/chat/search
- Offset pagination only for admin tables
- UTC timestamps
- ISO 8601
- Stable public IDs using UUIDv7 or ULID
- Never expose sequential internal IDs

### Database
- Use `created_at`, `updated_at`
- Use soft delete only where restoration/audit is required
- Add unique and check constraints
- Add indexes based on query patterns
- Use explicit enum values
- Use transactions for state transitions
- Use outbox table for events

### Security
- Central authorization
- Deny by default
- Rate-limit sensitive endpoints
- Validate all file uploads
- Avoid logging secrets or message bodies
- Record audit events for admin and sensitive actions

### Testing
- Unit tests for services
- Integration tests for API and database
- E2E tests for major flows
- Test access-control failures
- Test idempotency
- Test state-machine invalid transitions

---

## 5. Milestone 0 — Repository and Foundation

### Deliverables
- Monorepo
- Docker Compose
- FastAPI service
- Next.js service
- Admin app shell
- PostgreSQL
- PostGIS extension
- Redis
- Object-storage emulator
- Worker process
- Environment configuration
- Structured logging
- Error handling
- Health endpoints
- CI pipeline
- Linting
- Type checking
- Test harness

### Backend tasks
- Create application factory
- Create configuration module
- Create async database session
- Create Redis client
- Create health endpoints:
  - `/health/live`
  - `/health/ready`
- Create global exception handlers
- Add request ID middleware
- Add OpenTelemetry hooks
- Add base model mixins
- Add Alembic

### Web tasks
- Next.js application shell
- Responsive layout
- Design tokens
- Authentication placeholders
- API client package
- Global error boundary
- Loading and empty states

### Acceptance criteria
- `docker compose up` starts all local services
- API readiness checks database and Redis
- CI runs backend and frontend tests
- Database migrations apply from empty database
- One example endpoint is tested end to end

---

## 6. Milestone 1 — Identity and Profiles

### Data models
- User
- UserProfile
- UserSession
- UserDevice
- SocialAccount
- UserVerification
- UserPreference
- UserBlock
- ConsentRecord
- AuditLog

### Features
- Email/password signup
- Email verification
- Login
- Refresh token rotation
- Logout
- Logout all
- Password reset
- Google OAuth
- Apple-ready provider abstraction
- Mobile verification placeholder
- Session list
- Device list
- Profile edit
- Privacy settings
- Block user
- Delete account request
- Data export request

### API
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/logout-all`
- `POST /auth/verify-email`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `GET /users/me`
- `PATCH /users/me`
- `GET /users/{user_id}`
- `POST /users/{user_id}/block`
- `DELETE /users/{user_id}/block`
- `GET /users/me/sessions`
- `DELETE /users/me/sessions/{session_id}`

### Acceptance criteria
- Access tokens expire
- Refresh token reuse is detected
- Blocked users cannot initiate chat
- Private profile fields are never returned publicly
- OAuth account linking is protected
- Unit and integration tests pass

---

## 7. Milestone 2 — Book Catalog and Categories

### Data models
- Book
- BookEdition
- Author
- BookAuthor
- Publisher
- Category
- BookCategory
- BookIdentifier
- AcademicMetadata

### Features
- Manual catalog entry
- ISBN lookup abstraction
- Category tree
- Genre tags
- Academic metadata
- Duplicate edition detection
- Admin metadata correction

### API
- `GET /books`
- `GET /books/{book_id}`
- `POST /books/resolve-isbn`
- `GET /categories`
- `GET /authors`
- `GET /publishers`

### Acceptance criteria
- Multiple listings can point to one edition
- ISBN uniqueness is enforced
- Category hierarchy supports arbitrary depth
- Catalog service can later swap external metadata providers

---

## 8. Milestone 3 — Listings and Media

### Data models
- Listing
- ListingImage
- ListingCondition
- ListingLocation
- ListingDeliveryMethod
- ListingPriceHistory
- ListingInventory
- MediaAsset

### Features
- Draft listing
- Create from ISBN
- Add actual photos
- Condition details
- Sale/exchange/donation/request
- Price
- Negotiability
- Location
- Pickup/shipping
- Publish
- Edit
- Pause
- Relist
- Delete
- Expire
- Listing quality score

### State machine
- Draft
- Pending moderation
- Active
- Reserved
- Completed
- Expired
- Suspended
- Rejected
- Deleted

### API
- `POST /listings`
- `GET /listings/{listing_id}`
- `PATCH /listings/{listing_id}`
- `POST /listings/{listing_id}/publish`
- `POST /listings/{listing_id}/pause`
- `POST /listings/{listing_id}/relist`
- `DELETE /listings/{listing_id}`
- `POST /media/upload-url`
- `POST /media/{media_id}/complete`

### Acceptance criteria
- Only owner can modify
- Exact location is not public
- Media is not public before scan/processing
- Invalid state transitions fail
- Price history is preserved
- Tests cover every listing type

---

## 9. Milestone 4 — Search, Location, and Discovery

### Features
- PostgreSQL full-text search
- Trigram matching
- PostGIS radius search
- Autocomplete
- Filters
- Sorting
- Saved searches
- Wishlist
- Favorites
- Following
- Match notifications

### API
- `GET /search/listings`
- `GET /search/suggestions`
- `POST /saved-searches`
- `GET /saved-searches`
- `POST /wishlists/{book_id}`
- `DELETE /wishlists/{book_id}`
- `POST /listings/{listing_id}/favorite`
- `DELETE /listings/{listing_id}/favorite`
- `POST /follows`
- `DELETE /follows/{follow_id}`

### Acceptance criteria
- Search supports title, author, ISBN, category, location
- Distance sort uses PostGIS
- Public results expose approximate location only
- Zero-result searches are recorded
- Search query plans use indexes
- P95 target documented and load-tested

---

## 10. Milestone 5 — Chat and Notifications

### Data models
- ChatRequest
- Conversation
- ConversationMember
- Message
- MessageAttachment
- MessageRead
- Notification
- NotificationPreference
- NotificationDelivery

### Features
- Chat request
- Accept
- Decline
- Block
- Real-time text
- Image attachment
- Listing card
- Typing
- Read receipt
- Mute
- Archive
- Report
- In-app notification
- Email notification
- Push abstraction

### API
- `POST /chat-requests`
- `POST /chat-requests/{id}/accept`
- `POST /chat-requests/{id}/decline`
- `GET /conversations`
- `GET /conversations/{id}/messages`
- `POST /conversations/{id}/messages`
- WebSocket `/ws/conversations`
- `GET /notifications`
- `PATCH /notification-preferences`

### Acceptance criteria
- Unauthorized users cannot read conversations
- Blocked users cannot send requests
- Messages persist before acknowledgement
- Duplicate client message IDs do not create duplicates
- Notification delivery is asynchronous
- WebSocket reconnect does not lose messages

---

## 11. Milestone 6 — Offers, Pickup, and Reviews

### Data models
- Offer
- ExchangeOfferItem
- PickupSession
- Transaction
- Review
- ReviewDimension

### Features
- Price offer
- Counteroffer
- Exchange
- Bundle offer
- Expiration
- Accept/reject/withdraw
- Reserve listing
- Pickup proposal
- Handover code
- Complete transaction
- Transaction-linked review

### API
- `POST /offers`
- `POST /offers/{id}/counter`
- `POST /offers/{id}/accept`
- `POST /offers/{id}/reject`
- `POST /offers/{id}/withdraw`
- `POST /pickups`
- `POST /pickups/{id}/confirm`
- `POST /transactions/{id}/complete`
- `POST /reviews`

### Acceptance criteria
- Accepted offer reserves inventory atomically
- Two buyers cannot reserve the same last copy
- Reviews require completed transaction
- Each side can review once
- Pickup exact location is gated
- Expired offers cannot be accepted

---

## 12. Milestone 7 — Trust, Reports, and Admin Moderation

### Data models
- Report
- ModerationCase
- ModerationAction
- RiskEvent
- DeviceRisk
- CopyrightClaim

### Features
- Report user
- Report listing
- Report message
- Moderation queue
- Warning
- Remove content
- Suspend
- Ban
- Appeal
- Audit log
- Basic fraud rules
- Copyright workflow

### Admin screens
- Report queue
- User details
- Listing details
- Conversation evidence access with audit
- Moderation history
- Appeals
- Rule configuration

### Acceptance criteria
- Every moderator action is audited
- Support cannot browse private conversations without case context
- High-severity reports are prioritized
- Appeals preserve original evidence
- Suspensions enforce immediately

---

## 13. Milestone 8 — Communities

### Data models
- Community
- CommunityMember
- CommunityRole
- CommunityRule
- CommunityChannel
- CommunityPost
- PostComment
- PostReaction
- CommunityReport

### Features
- Create community
- Public/private/secret
- Join request
- Roles
- Feed
- Posts
- Comments
- Reactions
- Polls
- Pin
- Announcements
- Community marketplace tab
- Moderation
- Discovery by location, institution, genre, and book

### API
- `POST /communities`
- `GET /communities`
- `GET /communities/{id}`
- `POST /communities/{id}/join`
- `POST /communities/{id}/approve-member`
- `POST /communities/{id}/posts`
- `GET /communities/{id}/feed`
- `POST /posts/{id}/comments`
- `POST /posts/{id}/reactions`

### Acceptance criteria
- Secret communities are not discoverable
- Private content is permission protected
- Moderators can act only within assigned communities
- Institution communities can require verified membership
- Marketplace tab filters listings by community scope

---

## 14. Milestone 9 — Book Clubs, Buddy Reads, and Events

### Data models
- BookClub
- ClubBook
- BookNomination
- BookVote
- ReadingMilestone
- BuddyRead
- Readalong
- Event
- EventRSVP
- EventWaitlist
- EventCheckin

### Features
- Book nomination
- Voting
- Current/next/past books
- Reading milestones
- Chapter discussions
- Spoiler protection
- Buddy reads
- Readalongs
- Event creation
- RSVP
- Capacity
- Waitlist
- Calendar export
- QR check-in

### Acceptance criteria
- Spoiler content is hidden based on reader progress
- Voting rules are deterministic
- Capacity changes update waitlist safely
- Event time zones are correct
- Club book automatically links available marketplace listings

---

## 15. Milestone 10 — Reading Tracker

### Data models
- Shelf
- ShelfItem
- ReadingProgress
- ReadingNote
- ReadingGoal
- ReadingStatistic

### Features
- Shelves
- Current page
- Percentage
- Start/finish
- Notes
- Highlights
- Goals
- Streaks
- Year summary
- Community challenges

### Acceptance criteria
- Progress updates are idempotent
- Private notes never appear publicly
- Statistics can be recomputed
- Reading goals handle time zones
- Challenges respect membership rules

---

## 16. Milestone 11 — Payments, Orders, Shipping

### Data models
- Cart
- CartItem
- Order
- OrderItem
- Payment
- Payout
- Refund
- Shipment
- Dispute
- WebhookEvent
- IdempotencyKey

### Features
- Seller-specific cart
- Checkout
- Payment provider abstraction
- Seller payout
- Refund
- Shipping provider abstraction
- Tracking
- Buyer protection
- Disputes
- Evidence
- Webhooks

### Acceptance criteria
- Webhooks are signed and idempotent
- Payment state transitions are valid
- Duplicate callbacks do not duplicate orders/refunds
- Payout never exceeds captured funds
- Buyer protection release is auditable
- Provider outages degrade safely

---

## 17. Milestone 12 — Professional Sellers and Monetization

### Data models
- BusinessProfile
- BusinessLocation
- StaffAccount
- InventoryImport
- SubscriptionPlan
- Subscription
- Promotion
- PromotionOrder
- Coupon

### Features
- Storefront
- Staff roles
- Multi-location inventory
- CSV import
- Bulk edit
- Analytics
- Seller Pro
- Community Pro
- Institution plan
- Paid listing boosts
- Coupons

### Acceptance criteria
- Staff permissions are scoped
- Import is idempotent
- Failed rows are downloadable
- Promotions are clearly labeled
- Subscription entitlements are centralized
- Expired subscriptions remove premium access safely

---

## 18. Milestone 13 — Institutions and Donations

### Data models
- Institution
- InstitutionDomain
- InstitutionMember
- DonationCampaign
- DonationNeed
- DonationPledge
- DonationReceipt

### Features
- College verification
- Campus groups
- Campus marketplace
- Library profiles
- NGO campaigns
- Donation tracking
- Impact summaries

### Acceptance criteria
- Domain verification cannot grant institution admin automatically
- Campaign condition rules are enforced
- Donation confirmation requires recipient action
- Public impact data excludes donor private data

---

## 19. Milestone 14 — Recommendations and AI Assistance

### Features
- Rule-based recommendations first
- Search-based similar books
- Community recommendations
- Listing description assistance
- Category suggestions
- Price suggestions
- Condition suggestions
- Fraud prioritization

### AI rules
- Human confirmation required
- Store model/provider/version
- Record confidence
- Never auto-ban solely from AI output
- Allow user correction
- Avoid generating unsupported book metadata

### Acceptance criteria
- Recommendations have explanations
- AI failures do not block listing creation
- Suggested data is visibly editable
- Moderation AI only prioritizes review

---

## 20. Frontend Page Inventory

### Public web
- Home
- Search
- Listing details
- Book details
- Seller profile
- Community details
- Event details
- Sign in
- Register
- Help
- Safety
- Terms
- Privacy

### User web/mobile
- Dashboard
- Create listing
- My listings
- Listing editor
- Favorites
- Wishlists
- Saved searches
- Inbox
- Offers
- Orders
- Sales
- Purchases
- Exchanges
- Pickup
- Notifications
- Communities
- Book clubs
- Events
- Reading tracker
- Shelves
- Reviews
- Profile
- Verification
- Subscription
- Settings
- Support

### Admin
- Dashboard
- Users
- Listings
- Reports
- Moderation cases
- Appeals
- Communities
- Events
- Payments
- Refunds
- Payouts
- Shipping issues
- Categories
- Book metadata
- Promotions
- Subscriptions
- Notifications
- Feature flags
- Audit logs
- Support tickets
- Analytics

---

## 21. Required State Machines

Codex must implement explicit state machines for:

- Listing
- Offer
- Order
- Payment
- Shipment
- Dispute
- Verification
- Moderation case
- Subscription
- Donation pledge
- Event RSVP

Every transition needs:
- Source state
- Target state
- Actor
- Permission
- Validation
- Event
- Audit entry
- Test

---

## 22. Required Architecture Decision Records

Create ADRs for:

1. Modular monolith
2. PostgreSQL and PostGIS
3. Authentication token strategy
4. Direct-to-storage media upload
5. Transactional outbox
6. Search strategy
7. Payment provider abstraction
8. Shipping provider abstraction
9. WebSocket architecture
10. Audit logging
11. Child-safety model
12. Public location privacy
13. Review eligibility
14. Soft-delete policy
15. UUID/ULID public identifiers

---

## 23. Required CI Checks

Backend:
- Ruff format
- Ruff lint
- Mypy
- Pytest
- Migration consistency
- Dependency vulnerability scan

Frontend:
- ESLint
- TypeScript
- Unit tests
- Playwright smoke test
- Accessibility test
- Build

Infrastructure:
- Docker build
- IaC validation
- Secret scan
- Container scan

---

## 24. Local Development Commands

Create a root `Makefile` or task runner with:

```text
make setup
make up
make down
make migrate
make seed
make test
make lint
make typecheck
make e2e
make format
make api-docs
```

Also create sample seed data:
- Users
- Verified seller
- College
- Communities
- Books
- Listings
- Chat
- Offers
- Events
- Reading club

---

## 25. Codex Prompt for Starting the Project

Use this prompt in the repository:

```text
You are implementing OldPages.in.

First read:
1. docs/OLDPAGES_MASTER_BLUEPRINT.md
2. docs/CODEX_IMPLEMENTATION_PLAN.md

Implement only Milestone 0.

Requirements:
- Create the monorepo structure.
- Create a FastAPI application using async SQLAlchemy.
- Add PostgreSQL, PostGIS, Redis, and object-storage emulation in Docker Compose.
- Add Alembic.
- Add structured logging, request IDs, health endpoints, and global error responses.
- Create a Next.js web shell and admin shell.
- Add CI for lint, type check, tests, and builds.
- Add a root Makefile.
- Add unit and integration test scaffolding.
- Document setup in README.md.

Do not implement marketplace features yet.
Do not create microservices.
Do not skip tests.
At the end, report:
- Files created
- Commands to run
- Tests run
- Known limitations
```

---

## 26. Codex Prompt for Each Later Milestone

```text
Read the master blueprint and implementation plan.

Implement Milestone <NUMBER>: <NAME> only.

Before coding:
1. Inspect existing architecture and conventions.
2. List impacted modules.
3. List schema changes.
4. List API changes.
5. List authorization rules.
6. List tests.

During implementation:
- Keep business logic in services.
- Keep persistence in repositories.
- Add Alembic migrations.
- Add idempotency where required.
- Add audit events for sensitive actions.
- Add unit and integration tests.
- Update OpenAPI and docs.

After implementation:
- Run lint, type checks, tests, and build.
- Summarize changed files.
- Summarize data migrations.
- Summarize security considerations.
- List unresolved risks.
```

---

## 27. Release Checklist

Before each release:

- Migrations reviewed
- Backups verified
- Rollback plan ready
- Feature flags configured
- Secrets configured
- Rate limits configured
- Observability dashboards ready
- Alerts enabled
- Error budget understood
- Load test completed for critical paths
- Privacy review completed
- Security scan completed
- Accessibility smoke test completed
- Support documentation updated
- Admin tools ready
- Incident owner assigned

---

## 28. MVP Cut Line

The first public MVP includes:

- Identity
- Profile
- Catalog
- Listings
- Search
- Location
- Favorites
- Chat requests
- Chat
- Offers
- Pickup
- Reviews
- Reports
- Admin moderation

The first public MVP excludes:

- Integrated payments
- Shipping integrations
- Buyer protection
- Professional seller tools
- Full reading tracker
- Book clubs
- AI assistance
- Auctions
- Complex gamification
- Multi-seller cart
- Microservices

The architecture must support these later features without implementing them prematurely.

---

## 29. Final Instruction to Codex

Build a trustworthy, testable, secure product incrementally.

Do not optimize for the largest number of generated files. Optimize for:

- Correct business rules
- Strong authorization
- Clear module boundaries
- Reliable state transitions
- Excellent tests
- Safe user data handling
- Maintainable code
- Observable production behavior
