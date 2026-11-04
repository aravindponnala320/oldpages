# OldPages.in — Complete Application Flows & Architecture Document

**Version:** 1.0  
**Date:** 2026-06-25  
**Stack:** FastAPI · PostgreSQL/PostGIS · Redis · MinIO · Next.js · React 19

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Authentication Flows](#2-authentication-flows)
3. [Listing Lifecycle](#3-listing-lifecycle)
4. [Search & Discovery](#4-search--discovery)
5. [Chat & Messaging](#5-chat--messaging)
6. [Offer & Negotiation](#6-offer--negotiation)
7. [Order & Transaction](#7-order--transaction)
8. [Trust & Moderation](#8-trust--moderation)
9. [Reviews & Reputation](#9-reviews--reputation)
10. [Community Flows](#10-community-flows)
11. [Book Club Flows](#11-book-club-flows)
12. [Events Flow](#12-events-flow)
13. [Reading Tracker](#13-reading-tracker)
14. [Institution & Donation](#14-institution--donation)
15. [Professional Seller](#15-professional-seller)
16. [Recommendations & AI](#16-recommendations--ai)
17. [Notifications](#17-notifications)
18. [Admin & Moderation](#18-admin--moderation)
19. [Complete User Journey](#19-complete-user-journey)
20. [API Endpoint Reference](#20-api-endpoint-reference)
21. [Database Entity Map](#21-database-entity-map)
22. [Scope Summary](#22-scope-summary)

---

## 1. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                               CLIENTS                                     │
│                                                                           │
│   ┌────────────────────┐   ┌────────────────────┐   ┌─────────────────┐ │
│   │     Web App         │   │     Admin App       │   │  Mobile (future)│ │
│   │  Next.js 16 / React │   │  Next.js 16 / React │   │  Expo / RN      │ │
│   │  localhost:3000     │   │  localhost:3001     │   │  iOS / Android  │ │
│   └────────┬────────────┘   └────────┬────────────┘   └────────┬────────┘ │
└────────────┼─────────────────────────┼────────────────────────┼───────────┘
             │                         │                        │
             └─────────────────────────┼────────────────────────┘
                                       │ HTTPS / WebSocket
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Modular Monolith  (port 8000)                   │
│                                                                           │
│   /api/v1/auth          /api/v1/users         /api/v1/books              │
│   /api/v1/listings      /api/v1/search        /api/v1/chat               │
│   /api/v1/offers        /api/v1/orders        /api/v1/payments           │
│   /api/v1/shipments     /api/v1/disputes      /api/v1/communities        │
│   /api/v1/clubs         /api/v1/events        /api/v1/reading            │
│   /api/v1/institutions  /api/v1/donations     /api/v1/recommendations    │
│   /api/v1/business      /api/v1/subscriptions /api/v1/admin              │
│   WebSocket: /ws/conversations                                            │
│                                                                           │
│   Middleware: RequestID · CORS · OpenTelemetry · RFC-7807 Errors          │
└─────┬──────────────┬──────────────┬───────────────┬───────────────────────┘
      │              │              │               │
      ▼              ▼              ▼               ▼
 ┌─────────┐   ┌──────────┐  ┌──────────┐  ┌──────────────────┐
 │PostgreSQL│   │  Redis   │  │  MinIO   │  │  Worker Process  │
 │+PostGIS  │   │          │  │ (S3-compat│  │  Background Jobs │
 │ :5432    │   │ Cache    │  │  :9000   │  │                  │
 │          │   │ Sessions │  │ Media    │  │ • Email delivery  │
 │ 103+     │   │ WebSocket│  │ Storage  │  │ • Push notifs     │
 │ tables   │   │ Pub/Sub  │  │          │  │ • Outbox events   │
 │ 15 migr. │   │  :6379   │  │ Console  │  │ • Offer expiry    │
 └─────────┘   └──────────┘  │  :9001   │  │ • Media process   │
                              └──────────┘  └──────────────────┘
```

### Module Dependency Graph

```
identity ◄── users ◄── catalog ◄── listings ◄── search
                                        │
                              ┌─────────┼──────────┐
                              ▼         ▼          ▼
                            chat     commerce   trust
                              │         │
                              ▼         ▼
                       notifications  payments
                                       │
                              ┌────────┼───────────┐
                              ▼        ▼           ▼
                         business  subscriptions  donations
                                                  institutions
                                                  recommendations
                              communities ◄── clubs ◄── reading
```

---

## 2. Authentication Flows

### 2a. Email/Password Registration

```
User                    Web App (Next.js)               FastAPI                   Database
 │                           │                              │                          │
 │  Open /register           │                              │                          │
 │──────────────────────────▶│                              │                          │
 │                           │                              │                          │
 │  Fill form:               │                              │                          │
 │  • display_name           │                              │                          │
 │  • email                  │                              │                          │
 │  • password               │                              │                          │
 │  • confirm_password       │                              │                          │
 │  Submit                   │                              │                          │
 │──────────────────────────▶│                              │                          │
 │                           │  POST /api/v1/auth/register  │                          │
 │                           │─────────────────────────────▶│                          │
 │                           │  {display_name, email,       │  Hash password (Argon2id)│
 │                           │   password}                  │─────────────────────────▶│
 │                           │                              │  INSERT user             │
 │                           │                              │  INSERT user_profile     │
 │                           │                              │  INSERT user_preferences │
 │                           │                              │  INSERT consent_record   │
 │                           │                              │  CREATE session          │
 │                           │                              │  CREATE refresh_token    │
 │                           │  {access_token (15min),      │◀─────────────────────────│
 │                           │   refresh_token (30d),       │                          │
 │                           │   user: {id, name, email}}   │                          │
 │                           │◀─────────────────────────────│                          │
 │                           │  Store in localStorage:      │                          │
 │                           │  op_access_token             │                          │
 │                           │  op_refresh_token            │                          │
 │  Redirect → /dashboard    │                              │                          │
 │◀──────────────────────────│                              │                          │
 │                           │                              │                          │
 │  [Email arrives]          │                              │  (Background job:        │
 │  Click verify link        │                              │   queue email delivery)  │
 │──────────────────────────▶│  POST /auth/verify-email     │                          │
 │                           │─────────────────────────────▶│  UPDATE user             │
 │                           │                              │  email_verified = true   │
 │  ✅ Email verified         │◀─────────────────────────────│◀─────────────────────────│
```

### 2b. Login Flow

```
User              Web App                  FastAPI                   Database
 │                   │                        │                          │
 │  POST /login       │                        │                          │
 │──────────────────▶│                        │                          │
 │  {email,          │  POST /auth/login       │                          │
 │   password}       │────────────────────────▶│                          │
 │                   │                        │  SELECT user by email    │
 │                   │                        │─────────────────────────▶│
 │                   │                        │  Verify Argon2id hash    │
 │                   │                        │  Check account status    │
 │                   │                        │  (not suspended/banned)  │
 │                   │                        │  INSERT user_session     │
 │                   │                        │  INSERT refresh_token    │
 │                   │                        │  INSERT audit_log        │
 │                   │  {access_token,        │◀─────────────────────────│
 │                   │   refresh_token,       │                          │
 │                   │   user}                │                          │
 │                   │◀───────────────────────│                          │
 │  /dashboard       │  localStorage.set()    │                          │
 │◀──────────────────│                        │                          │
```

### 2c. Token Refresh (Automatic)

```
Web App (every ~14 min)           FastAPI                   Database
         │                            │                          │
         │  POST /auth/refresh        │                          │
         │  {refresh_token}           │                          │
         │───────────────────────────▶│                          │
         │                            │  Find token in DB        │
         │                            │─────────────────────────▶│
         │                            │  Check not revoked       │
         │                            │  Check not expired       │
         │                            │  INVALIDATE old token    │
         │                            │  CREATE new refresh token│
         │                            │  (rotation)              │
         │  {new_access_token,        │◀─────────────────────────│
         │   new_refresh_token}       │                          │
         │◀───────────────────────────│                          │
         │  Update localStorage       │                          │
         │                            │                          │
         │  ⚠️  Reuse detected:        │                          │
         │  Old refresh used again → REVOKE all sessions        │
         │  Force re-login (security)                           │
```

### 2d. OAuth (Google Sign-In)

```
User         Web App              FastAPI            Google OAuth
 │               │                    │                    │
 │  Click        │                    │                    │
 │  "Sign in     │                    │                    │
 │  with Google" │                    │                    │
 │──────────────▶│  Generate state    │                    │
 │               │  + PKCE verifier   │                    │
 │               │  Redirect to Google│                    │
 │               │────────────────────────────────────────▶│
 │               │                    │                    │
 │  [User        │                    │                    │
 │   consents]   │                    │                    │
 │               │                    │  callback?         │
 │               │                    │  code=xxx&state=yyy│
 │               │◀───────────────────────────────────────│
 │               │  POST /auth/oauth/ │                    │
 │               │  google            │                    │
 │               │  {code, state,     │                    │
 │               │   verifier}        │                    │
 │               │───────────────────▶│                    │
 │               │                    │  Verify state      │
 │               │                    │  Exchange code for │
 │               │                    │  Google token      │
 │               │                    │  Get user profile  │
 │               │                    │  Link/create       │
 │               │  {tokens, user}    │  social_account    │
 │               │◀───────────────────│                    │
 │  /dashboard   │                    │                    │
 │◀──────────────│                    │                    │
```

### 2e. Session & Device Management

```
User                  Web App                FastAPI
 │                       │                      │
 │  GET /users/me/        │                      │
 │  sessions             │                      │
 │──────────────────────▶│──────────────────────▶│
 │  [{id, device,        │                      │  SELECT user_sessions
 │    ip, last_active,   │                      │  WHERE user_id = me
 │    current: true}]    │◀─────────────────────│
 │◀──────────────────────│                      │
 │                       │                      │
 │  DELETE /sessions/{id}│                      │
 │  (log out device)     │──────────────────────▶│
 │──────────────────────▶│                      │  REVOKE session
 │                       │                      │  + refresh tokens
 │                       │                      │
 │  POST /auth/logout-all│                      │
 │  (nuclear option)     │──────────────────────▶│
 │──────────────────────▶│                      │  REVOKE all sessions
 │  Redirect /           │◀─────────────────────│  Clear localStorage
```

---

## 3. Listing Lifecycle

### 3a. Create Listing (Full 5-Step Flow)

```
Seller                       Web App (5-step form)               FastAPI              Database
  │                                  │                               │                    │
  │  STEP 1: FIND BOOK               │                               │                    │
  │  Type title or ISBN              │                               │                    │
  │─────────────────────────────────▶│  GET /books?q=physics         │                    │
  │                                  │──────────────────────────────▶│  Full-text search  │
  │  Select from results             │  [{id, title, author, ISBN,   │◀───────────────────│
  │◀─────────────────────────────────│   cover, publisher}]          │                    │
  │                                  │◀──────────────────────────────│                    │
  │                                  │                               │                    │
  │  STEP 2: LISTING TYPE            │                               │                    │
  │  ○ Sell  ○ Exchange              │                               │                    │
  │  ○ Donate  ○ Lend                │                               │                    │
  │  ○ Request  ○ Giveaway           │                               │                    │
  │                                  │                               │                    │
  │  STEP 3: CONDITION DETAILS       │                               │                    │
  │  Condition: [Excellent ▼]        │                               │                    │
  │  ☑ Has highlighting (20%)        │                               │                    │
  │  ☐ Torn pages                    │                               │                    │
  │  ☑ Name written inside           │                               │                    │
  │  ☐ Water damage                  │                               │                    │
  │  ☐ Missing pages                 │                               │                    │
  │  Notes: [                  ]     │                               │                    │
  │                                  │                               │                    │
  │  STEP 4: PRICE & DELIVERY        │                               │                    │
  │  Price (₹): [350]                │                               │                    │
  │  ☑ Negotiable                    │                               │                    │
  │  ☑ Pickup available              │                               │                    │
  │  ○ Shipping available            │                               │                    │
  │  City: [Bangalore]               │                               │                    │
  │                                  │                               │                    │
  │  STEP 5: PHOTOS + SUBMIT         │                               │                    │
  │  Upload photos                   │  POST /media/upload-url       │                    │
  │─────────────────────────────────▶│──────────────────────────────▶│  INSERT media_asset│
  │                                  │  {upload_url, media_id}       │  status=pending    │
  │                                  │◀──────────────────────────────│◀───────────────────│
  │  PUT photos directly to MinIO    │                               │                    │
  │─────────────────────────────────────────────────────────────────────────▶ MinIO       │
  │                                  │  POST /media/{id}/complete    │                    │
  │                                  │──────────────────────────────▶│  UPDATE media=     │
  │                                  │                               │  processing        │
  │                                  │  POST /listings               │                    │
  │  Submit form                     │──────────────────────────────▶│  INSERT listing    │
  │─────────────────────────────────▶│  {book_id, listing_type,      │  status=draft      │
  │                                  │   condition, price_cents,     │  INSERT condition  │
  │                                  │   fulfillment, location}      │  INSERT location   │
  │                                  │  {listing_id, status:draft}   │◀───────────────────│
  │                                  │◀──────────────────────────────│                    │
  │                                  │  POST /listings/{id}/publish  │                    │
  │                                  │──────────────────────────────▶│  UPDATE status=    │
  │                                  │                               │  active            │
  │  ✅ Listing is LIVE!              │◀──────────────────────────────│  INSERT price_hist │
  │◀─────────────────────────────────│                               │◀───────────────────│
```

### 3b. Listing State Machine

```
                         ┌─────────────────┐
                         │      DRAFT       │
                         │  (saved form)    │
                         └────────┬─────────┘
                                  │ seller publishes
                                  ▼
                    ┌─────────────────────────────┐
                    │      PENDING MODERATION      │
                    │  (auto-approve in local dev) │
                    └─────────────┬───────────────┘
                                  │ approved by moderator
                                  ▼
                    ┌─────────────────────────────┐
          ┌─────────│           ACTIVE            │─────────────┐
          │         └───────────┬─────────────────┘             │
          │                     │                               │
     seller pauses         expires (no                    offer accepted +
          │                activity)                      inventory reserved
          ▼                     ▼                               ▼
    ┌──────────┐          ┌──────────┐                   ┌──────────────┐
    │  PAUSED  │          │ EXPIRED  │                   │   RESERVED   │
    └────┬─────┘          └──────────┘                   └──────┬───────┘
         │ seller relists                                        │ transaction
         │                                              completed/cancelled
         └────────────────▶ ACTIVE                             │
                                                               ▼
                                                        ┌──────────────┐
                                                        │  COMPLETED   │
                                                        └──────────────┘

  Moderator actions (any time from ACTIVE):
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │  SUSPENDED   │    │   REJECTED   │    │   DELETED    │
  │  (temporary) │    │  (content    │    │  (by seller  │
  │              │    │   violation) │    │   or admin)  │
  └──────────────┘    └──────────────┘    └──────────────┘
```

### 3c. Listing Quality Score

```
Score = sum of weighted signals (0 → 100):

  Photo count            → max +25 pts  (5 pts per photo, max 5)
  Image quality          → max +10 pts  (resolution check)
  Condition completeness → max +15 pts  (all fields filled)
  ISBN confidence        → max +20 pts  (verified ISBN = 20)
  Description filled     → max +10 pts  (>50 chars = 10)
  Price set              → max +10 pts
  Location set           → max +10 pts

  Score ≥ 80 → "Complete listing" badge shown
  Score < 40 → Warning shown to seller
```

---

## 4. Search & Discovery

### 4a. Search Query Flow

```
User Input                Web App              FastAPI Search              PostgreSQL
     │                       │                      │                           │
     │  Type "physics ncert  │                      │                           │
     │  class 12 bangalore"  │                      │                           │
     │──────────────────────▶│                      │                           │
     │                       │  GET /search/        │                           │
     │  Autocomplete appears │  suggestions?q=phys  │                           │
     │◀──────────────────────│──────────────────────▶  tsvector prefix match    │
     │  ["physics","physio"] │◀─────────────────────│◀──────────────────────────│
     │                       │                      │                           │
     │  Apply filters:       │                      │                           │
     │  ☑ Pickup available   │                      │                           │
     │  Condition: Good+     │                      │                           │
     │  Max price: ₹500      │                      │                           │
     │  Distance: 10km       │                      │                           │
     │  Sort: Nearest        │                      │                           │
     │──────────────────────▶│  GET /search/        │                           │
     │                       │  listings?           │                           │
     │                       │  q=physics+ncert...  │                           │
     │                       │  &condition=good     │                           │
     │                       │  &max_price_cents=   │                           │
     │                       │  50000               │                           │
     │                       │  &lat=12.97          │                           │
     │                       │  &lng=77.59          │                           │
     │                       │  &radius_km=10       │                           │
     │                       │  &sort=nearest       │                           │
     │                       │  &limit=24           │                           │
     │                       │──────────────────────▶                           │
     │                       │                      │  SELECT listings l        │
     │                       │                      │  JOIN books b ON          │
     │                       │                      │  l.book_id = b.id         │
     │                       │                      │  WHERE                    │
     │                       │                      │  plainto_tsquery(         │
     │                       │                      │  'physics ncert')         │
     │                       │                      │  @@ l.search_document     │
     │                       │                      │  AND l.status = 'active'  │
     │                       │                      │  AND l.condition IN       │
     │                       │                      │  ('good','excellent',     │
     │                       │                      │  'like_new','new')        │
     │                       │                      │  AND l.price_cents ≤      │
     │                       │                      │  50000                    │
     │                       │                      │  AND ST_DWithin(          │
     │                       │                      │  location,                │
     │                       │                      │  ST_Point(77.59,12.97),   │
     │                       │                      │  10000)  ← meters         │
     │                       │                      │  ORDER BY                 │
     │                       │                      │  ST_Distance(location,    │
     │                       │                      │  ST_Point(77.59,12.97))   │
     │                       │                      │──────────────────────────▶│
     │                       │                      │                           │
     │  Results:             │◀─────────────────────│◀──────────────────────────│
     │  • 8 listings         │                      │                           │
     │  • Approx. location   │                      │  ⚠️  PRIVACY:              │
     │    (no exact address  │                      │  Exact coords hidden      │
     │    until purchase)    │                      │  Only area shown          │
     │◀──────────────────────│                      │  publicly                 │
```

### 4b. Search Ranking Signals

```
┌──────────────────────────────────────────────────────────┐
│               SEARCH RANKING (Combined Score)             │
│                                                           │
│  1. Text Relevance        [0-40 pts]                      │
│     • tsvector rank vs query                             │
│     • Title match > description match                    │
│     • ISBN exact match = top score                       │
│                                                           │
│  2. Distance              [0-20 pts]                      │
│     • PostGIS ST_Distance                                │
│     • 0-2km = 20pts, 2-5km = 15pts, 5-10km = 10pts      │
│                                                           │
│  3. Freshness             [0-15 pts]                      │
│     • < 1 day old = 15pts                                │
│     • < 1 week = 10pts, < 1 month = 5pts                 │
│                                                           │
│  4. Condition Quality     [0-10 pts]                      │
│     • new_sealed=10, like_new=9, excellent=8...          │
│                                                           │
│  5. Seller Trust Score    [0-10 pts]                      │
│     • Verified + high rating = 10pts                     │
│                                                           │
│  6. Listing Quality Score [0-5 pts]                       │
│     • Complete listings (photos + desc) boosted          │
│                                                           │
│  7. Promotion Score       [clearly labelled]              │
│     • Paid boosts applied transparently                  │
│     • Never overrides safety/relevance                   │
└──────────────────────────────────────────────────────────┘
```

### 4c. Wishlist & Saved Search Alerts

```
User saves search:
  POST /saved-searches
  {query: "NCERT Physics", filters: {city:"Bangalore"}}

New matching listing added → Worker detects match →
  🔔 Notification: "New listing matches your search!"

User adds book to wishlist:
  POST /wishlists/{book_id}

Listing for that book goes live → Worker detects →
  🔔 Notification: "A copy of your wishlisted book is available!"

User follows seller:
  POST /follows {followee_id: "seller_xyz"}

Seller adds new listing → 
  🔔 Notification: "BookNook Store listed 3 new books"
```

---

## 5. Chat & Messaging

### 5a. Chat Request Initiation

```
Buyer                    Web App                 FastAPI              Seller
  │                         │                       │                    │
  │  View listing           │                       │                    │
  │  Click "Message Seller" │                       │                    │
  │────────────────────────▶│                       │                    │
  │                         │  Check: is user       │                    │
  │                         │  authenticated?       │                    │
  │                         │  Check: not self      │                    │
  │                         │  Check: not blocked   │                    │
  │                         │                       │                    │
  │                         │  POST /chat-requests  │                    │
  │                         │  {listing_id,         │                    │
  │                         │   message: "Hi! Is    │                    │
  │                         │   this still          │                    │
  │                         │   available?"}        │                    │
  │                         │──────────────────────▶│                    │
  │                         │                       │  INSERT            │
  │                         │                       │  chat_request      │
  │                         │                       │  status=pending    │
  │  "Request sent,         │  {id, status:pending} │                    │
  │   awaiting response"    │◀──────────────────────│  🔔 Notify seller  │
  │◀────────────────────────│                       │───────────────────▶│
  │                         │                       │                    │
  │  (Seller can:           │                       │                    │
  │   accept / decline /    │                       │                    │
  │   block)                │                       │                    │
  │                         │                       │  POST /chat-       │
  │                         │                       │  requests/{id}/    │
  │                         │                       │  accept            │
  │                         │                       │◀───────────────────│
  │                         │                       │  CREATE            │
  │  🔔 Chat open!           │                       │  conversation      │
  │◀────────────────────────│                       │  + members         │
  │  Navigate to /inbox/{id}│                       │                    │
```

### 5b. Real-Time WebSocket Chat

```
Browser (Buyer)              FastAPI WebSocket           Browser (Seller)
      │                             │                           │
      │  WS connect:                │                           │
      │  ws://api/ws/               │                           │
      │  conversations?             │                           │
      │  token=<JWT>                │                           │
      │────────────────────────────▶│                           │
      │                             │  Verify JWT               │
      │                             │  Register conn in Redis   │
      │  ✅ Connected                │  (user_id → socket_id)   │
      │◀────────────────────────────│                           │
      │                             │                           │
      │  {type: "message",          │                           │
      │   conversation_id: "c1",    │                           │
      │   content: "Is ₹300 ok?",   │                           │
      │   client_message_id: "m_1"} │                           │
      │────────────────────────────▶│                           │
      │                             │  INSERT message DB        │
      │                             │  (idempotency on          │
      │                             │   client_message_id)      │
      │                             │  Lookup seller socket     │
      │                             │  from Redis               │
      │  {type: "message_ack",      │                           │
      │   id: "db_id",              │  Fan-out to seller        │
      │   client_message_id: "m_1"} │  WebSocket connection     │
      │◀────────────────────────────│──────────────────────────▶│
      │                             │                           │  
      │                             │  If seller offline:       │
      │                             │  INSERT notification      │
      │                             │  Queue push/email         │
      │                             │                           │
      │  (Reconnect after drop)     │                           │
      │  GET /conversations/{id}/   │                           │
      │  messages?after=last_id     │                           │
      │────────────────────────────▶│  Replay missed messages   │
      │◀────────────────────────────│                           │
```

### 5c. Message Types in Conversation

```
┌──────────────────────────────────────────────────────────┐
│  Conversation: "Physics NCERT Class 12"                   │
│                                                           │
│  👤 Rahul                              2:30 PM ✓✓       │
│  "Hi! Is this still available?"                          │
│                                                           │
│                      "Yes! Pick up from Koramangala" 2:32│
│                                                  [You] ✓ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  💰 OFFER CARD                                       │ │
│  │  ₹320 for "Physics Part II" (was ₹350)             │ │
│  │  Fulfillment: Pickup                                │ │
│  │  Expires: 48 hours                                  │ │
│  │  [Accept ✓]  [Counter ↕]  [Decline ✗]             │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  📍 PICKUP SESSION                                   │ │
│  │  📅 Saturday, 3:00 PM – 5:00 PM                    │ │
│  │  📌 Indiranagar Starbucks                           │ │
│  │  🔑 Handover Code: XK7P2                           │ │
│  │  [Confirmed ✓]                                      │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  ⭐ REVIEW REQUEST                                   │ │
│  │  Transaction complete! How was your experience?     │ │
│  │  [Leave Review]                                     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  [📎 Attach]  [Type a message...]           [Send ▶]    │
└──────────────────────────────────────────────────────────┘
```

### 5d. Safety Features in Chat

```
Content Safety Pipeline:
  Message sent → 
    ├── Phone number pattern detect → Warn user
    ├── External link → Scan + warn
    ├── Spam phrase detection → Rate limit
    ├── Contact scraping → Block & alert
    └── Rate limiting: 50 msgs/hour per user

Report Message:
  POST /conversations/{id}/messages/{msg_id}/report
  {reason: "spam"|"harassment"|"unsafe_link"}
  → Creates message_report
  → Escalates to moderation if pattern found

Evidence Retention:
  Conversations in active disputes → NEVER deleted
  Moderator access → requires audit log entry
  GET /admin/conversations/{id}/evidence
  → INSERT audit_log (who accessed, why, when)
```

---

## 6. Offer & Negotiation

### 6a. Price Offer Flow

```
Buyer                     FastAPI                    Seller                    Database
  │                          │                          │                          │
  │  POST /offers            │                          │                          │
  │  {listing_id: "abc",     │                          │                          │
  │   offer_type: "price",   │                          │                          │
  │   amount_cents: 32000,   │                          │                          │
  │   quantity: 1,           │                          │                          │
  │   fulfillment: "pickup", │                          │                          │
  │   message: "Student,     │                          │                          │
  │   can you reduce?",      │                          │                          │
  │   expires_at: +48h}      │                          │                          │
  │─────────────────────────▶│                          │                          │
  │                          │  Validate:               │                          │
  │                          │  • Listing is active     │                          │
  │                          │  • Buyer ≠ Seller        │                          │
  │                          │  • Quantity available    │                          │
  │                          │  INSERT offer            │                          │
  │                          │  status=pending          │                          │
  │  {offer_id, status:      │─────────────────────────────────────────────────────▶│
  │   pending}               │  🔔 Notify seller        │                          │
  │◀─────────────────────────│─────────────────────────▶│                          │
  │                          │                          │                          │
  │                          │                          │  POST /offers/{id}/      │
  │                          │                          │  counter                 │
  │                          │                          │  {amount_cents: 34000,   │
  │                          │                          │   message: "Best I can do│
  │                          │                          │   as it's like new"}     │
  │                          │◀─────────────────────────│                          │
  │                          │  INSERT counter offer    │                          │
  │  🔔 Counteroffer!         │  parent_offer_id = orig  │                          │
  │◀─────────────────────────│──────────────────────────────────────────────────────▶│
  │                          │                          │                          │
  │  POST /offers/{id}/      │                          │                          │
  │  accept                  │                          │                          │
  │─────────────────────────▶│                          │                          │
  │                          │  BEGIN TRANSACTION       │                          │
  │                          │  UPDATE offer            │                          │
  │                          │  status=accepted         │                          │
  │                          │  SELECT listing_inventory│                          │
  │                          │  FOR UPDATE              │                          │
  │                          │  (pessimistic lock)      │                          │
  │                          │  Decrement quantity      │                          │
  │                          │  If qty=0: listing →     │                          │
  │                          │  RESERVED                │                          │
  │                          │  INSERT transaction      │                          │
  │                          │  COMMIT                  │                          │
  │  {transaction_id}        │─────────────────────────────────────────────────────▶│
  │◀─────────────────────────│  🔔 Notify both parties  │                          │
```

### 6b. Offer State Machine

```
                    ┌─────────────────────────────────────┐
                    │         Buyer creates offer          │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                             ┌───────────┐
                  ┌──────────│  PENDING  │──────────┐
                  │          └─────┬─────┘          │
                  │                │                │
             Buyer                 │           Buyer
             withdraws        Seller          withdraws
                  │           responds             │
                  ▼                │               ▼
           ┌──────────┐           │         ┌──────────┐
           │WITHDRAWN │    ┌──────┴──────┐   │ EXPIRED  │
           └──────────┘    │             │   │ (48h TTL)│
                           │             │   └──────────┘
                    Seller accepts  Seller rejects
                           │             │
                           ▼             ▼
                     ┌──────────┐  ┌──────────┐
                     │ ACCEPTED │  │ REJECTED │
                     └────┬─────┘  └──────────┘
                          │
                    Inventory reserved atomically
                    Transaction created
                          │
                  ┌───────┴────────────────────┐
                  │  Seller counters instead    │
                  ▼                             │
            ┌──────────┐                        │
            │COUNTERED │ ◄──── Loops until     │
            └────┬─────┘       deal or reject   │
                 │                              │
         Buyer accepts counter                  │
                 │                              │
                 └──────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  TRANSACTION  │
                  │    CREATED    │
                  └───────────────┘
```

### 6c. Exchange Offer

```
Buyer                              API
  │                                 │
  │  POST /offers                   │
  │  {offer_type: "exchange",       │
  │   listing_id: "seller_book_id", │
  │   exchange_items: [             │
  │     {                           │
  │       offered_listing_id:       │
  │       "my_listing_id",          │
  │       title: "Clean Code",      │
  │       condition_note: "Good,    │
  │       few highlights",          │
  │       cash_adjustment_cents:    │
  │       5000  ← ₹50 extra from me│
  │     }                           │
  │   ],                            │
  │   message: "Exchange + ₹50?"}   │
  │────────────────────────────────▶│
  │  {offer_id,                     │
  │   exchange_items: [{...}]}      │
  │◀────────────────────────────────│
```

### 6d. Bundle Offer

```
Buyer wants multiple books from same seller:
  POST /offers
  {offer_type: "bundle",
   listing_id: "primary_listing",
   bundle_listing_ids: ["book2_id", "book3_id"],
   amount_cents: 80000,  ← ₹800 for all 3
   message: "Bundle deal?"}
```

---

## 7. Order & Transaction

### 7a. Transaction States

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORDER STATE MACHINE                           │
│                                                                  │
│  CREATED ──────────────────────────────▶ AWAITING_PAYMENT       │
│     │                                         │                 │
│     │ (cash on pickup path)                   │ payment captured│
│     │                                         ▼                 │
│     │                                       PAID               │
│     │                                         │                 │
│     │                                         │ seller accepts  │
│     │                                         ▼                 │
│     │                                      ACCEPTED            │
│     │                                         │                 │
│     │                               ┌─────────┴──────────┐     │
│     │                          pickup              shipping     │
│     │                               │                    │     │
│     │                               ▼                    ▼     │
│     │                       READY_FOR_PICKUP          SHIPPED  │
│     │                               │                    │     │
│     │                               │               delivered  │
│     │                               │               (webhook)  │
│     │                               │                    ▼     │
│     │                               │               DELIVERED  │
│     │                               │                    │     │
│     └───────────────────────────────┴────────────────────┘     │
│                                     │ buyer confirms             │
│                                     ▼                           │
│                                 COMPLETED ──▶ Seller payout     │
│                                     │        Review prompt      │
│                                     │                           │
│  CANCELLED ◄──── any stage before SHIPPED                       │
│  REFUNDED  ◄──── after payment, before completion               │
│  DISPUTED  ◄──── buyer opens dispute (any post-payment stage)   │
└─────────────────────────────────────────────────────────────────┘
```

### 7b. Pickup Session Flow

```
Buyer                    FastAPI                  Seller
  │                         │                        │
  │  POST /pickups          │                        │
  │  {transaction_id,       │                        │
  │   proposed_start_at:    │                        │
  │   "2026-07-05T15:00Z",  │                        │
  │   proposed_end_at:      │                        │
  │   "2026-07-05T17:00Z",  │                        │
  │   public_location_label:│                        │
  │   "Koramangala          │                        │
  │    Starbucks, 80ft Rd"} │                        │
  │────────────────────────▶│                        │
  │                         │  INSERT pickup_session │
  │                         │  Generate handover_code│
  │  {pickup_id,            │  (cryptographic 5-char)│
  │   handover_code: "XK7P2"│                        │
  │   status: proposed}     │  🔔 Notify seller      │
  │◀────────────────────────│───────────────────────▶│
  │                         │                        │
  │  "Awaiting seller       │                        │  Seller views
  │   confirmation"         │                        │  pickup details
  │                         │                        │
  │                         │  POST /pickups/{id}/   │
  │                         │  confirm               │
  │                         │◀───────────────────────│
  │                         │  UPDATE pickup         │
  │                         │  status=confirmed      │
  │  🔔 Pickup confirmed!    │                        │
  │◀────────────────────────│                        │
  │                         │                        │
  │  ── Meet in person ──   │                        │
  │                         │                        │
  │  Buyer shows code "XK7P2"                        │
  │  Seller verifies                                 │
  │                         │                        │
  │  POST /transactions/    │                        │
  │  {id}/complete          │                        │
  │  {handover_code:"XK7P2"}│                        │
  │────────────────────────▶│                        │
  │                         │  Verify code matches   │
  │                         │  UPDATE transaction    │
  │                         │  status=completed      │
  │                         │  UPDATE listing=       │
  │                         │  COMPLETED             │
  │  ✅ Transaction done!    │  Queue payout          │
  │◀────────────────────────│  🔔 Both notified      │
```

### 7c. Payment Provider Flow

```
Buyer           FastAPI             Razorpay/UPI            Database
  │                │                     │                      │
  │  POST          │                     │                      │
  │  /payments/    │                     │                      │
  │  {order_id}/   │                     │                      │
  │  initiate      │                     │                      │
  │  {provider:    │                     │                      │
  │   "razorpay",  │                     │                      │
  │   idempotency_ │                     │                      │
  │   key: "uid1"} │                     │                      │
  │───────────────▶│                     │                      │
  │                │  Check idempotency  │                      │
  │                │  (duplicate check)  │                      │
  │                │  INSERT payment     │                      │
  │                │  status=pending     │                      │
  │                │  Call provider      │                      │
  │                │────────────────────▶│                      │
  │                │                     │  Create order/       │
  │                │  {payment_url,      │  payment_intent      │
  │                │  provider_payment_id│                      │
  │                │  amount: ₹350}      │                      │
  │                │◀────────────────────│                      │
  │  Redirect to   │                     │                      │
  │  payment page  │                     │                      │
  │◀───────────────│                     │                      │
  │                │                     │                      │
  │  [User pays    │                     │                      │
  │   via UPI/card]│                     │                      │
  │───────────────────────────────────────▶                     │
  │                │                     │  Payment captured    │
  │                │  POST /payments/    │                      │
  │                │  webhook/razorpay   │                      │
  │                │◀────────────────────│                      │
  │                │                     │                      │
  │                │  1. Verify HMAC     │                      │
  │                │     signature       │                      │
  │                │  2. Check idempotent│                      │
  │                │     (provider_event_│                      │
  │                │     id unique)      │                      │
  │                │  3. UPDATE payment  │                      │
  │                │     status=captured │                      │
  │                │  4. UPDATE order    │                      │
  │                │     status=paid     │                      │
  │                │  5. INSERT webhook_ │                      │
  │                │     event           │                      │
  │                │────────────────────────────────────────────▶│
  │  🔔 Payment    │                     │                      │
  │  confirmed!    │                     │                      │
  │◀───────────────│                     │                      │
```

### 7d. Dispute Flow

```
Buyer                  FastAPI                 Admin               Seller
  │                       │                      │                    │
  │  POST /disputes       │                      │                    │
  │  {order_id,           │                      │                    │
  │   reason:             │                      │                    │
  │   "item_not_as_       │                      │                    │
  │   described",         │                      │                    │
  │   description:        │                      │                    │
  │   "Book had water     │                      │                    │
  │   damage not shown    │                      │                    │
  │   in photos"}         │                      │                    │
  │──────────────────────▶│                      │                    │
  │                       │  INSERT dispute      │                    │
  │                       │  status=opened       │                    │
  │                       │  UPDATE order        │                    │
  │  {dispute_id,         │  status=disputed     │                    │
  │   status: opened}     │  Freeze payout       │                    │
  │◀──────────────────────│──────────────────────▶                   │
  │                       │                      │  🔔 New dispute    │
  │                       │                      │                    │
  │                       │                      │  Admin reviews:    │
  │                       │                      │  • Chat messages   │
  │                       │                      │  • Listing photos  │
  │                       │                      │  • Seller history  │
  │                       │                      │  • Buyer history   │
  │                       │                      │                    │
  │                       │                      │  POST /disputes/   │
  │                       │                      │  {id}/resolve      │
  │                       │                      │  {resolution:      │
  │                       │                      │   "resolved_buyer",│
  │                       │                      │   note: "Damage    │
  │                       │                      │   visible in seller│
  │                       │                      │   photos"}         │
  │                       │◀─────────────────────│                    │
  │                       │  UPDATE dispute=     │                    │
  │                       │  resolved_buyer      │                    │
  │                       │  Initiate refund     │                    │
  │  🔔 Refund initiated! │  Notify both         │  🔔 Payout blocked │
  │◀──────────────────────│──────────────────────────────────────────▶│
```

### 7e. Refund Flow

```
Trigger (dispute resolution / order cancellation)
     │
     ▼
POST /refunds (internal)
{payment_id, order_id, amount_cents, reason}
     │
     ▼
INSERT refund (status=pending)
     │
     ▼
Call payment_provider.refund_payment()
     │
     ├─ Success: UPDATE refund status=succeeded
     │           UPDATE payment status=refunded
     │           UPDATE order status=refunded
     │           🔔 Notify buyer
     │
     └─ Failure: UPDATE refund status=failed
                 Alert ops team
                 Retry via worker (exponential backoff)
```

---

## 8. Trust & Moderation

### 8a. Report → Moderation Pipeline

```
Reporter               FastAPI              Auto-Classifier       Moderator Queue
    │                     │                       │                     │
    │  POST /reports      │                       │                     │
    │  {target_type:      │                       │                     │
    │   "listing",        │                       │                     │
    │   target_id: "xyz", │                       │                     │
    │   reason: "fake_    │                       │                     │
    │   listing",         │                       │                     │
    │   description: "..."}                       │                     │
    │────────────────────▶│                       │                     │
    │                     │  INSERT report        │                     │
    │                     │  Classify severity:   │                     │
    │                     │───────────────────────▶                     │
    │  "Thank you for     │                       │  Severity rules:    │
    │   reporting"        │                       │  child_safety=CRIT  │
    │◀────────────────────│                       │  copyright=HIGH     │
    │                     │                       │  harassment=HIGH    │
    │                     │                       │  fake_listing=MED   │
    │                     │                       │  spam=LOW           │
    │                     │◀──────────────────────│                     │
    │                     │                       │                     │
    │                     │  if CRITICAL:         │                     │
    │                     │  Auto-restrict content│                     │
    │                     │  immediately          │                     │
    │                     │                       │                     │
    │                     │  CREATE moderation    │                     │
    │                     │  case                 │                     │
    │                     │  Assign to queue      │                     │
    │                     │─────────────────────────────────────────────▶│
    │                     │                       │  Moderator assigned │
    │                     │                       │  reviews case       │
    │                     │                       │  Takes action:      │
    │                     │                       │  • warn             │
    │                     │                       │  • remove_content   │
    │                     │                       │  • suspend_listing  │
    │                     │                       │  • suspend_user Nd  │
    │                     │                       │  • ban_permanent    │
    │                     │                       │  • dismiss          │
```

### 8b. Trust Score System

```
┌──────────────────────────────────────────────────────────┐
│                  USER TRUST SCORE (0–100)                 │
│                                                           │
│  POSITIVE SIGNALS:                                        │
│  ✅  Email verified              +10                      │
│  ✅  Phone verified              +15                      │
│  ✅  Identity verified           +20                      │
│  ✅  Account age > 6 months      +10                      │
│  ✅  Completed transactions      +5 each (max +50)        │
│  ✅  Avg rating ≥ 4.5            +20                      │
│  ✅  Avg rating 4.0–4.5          +10                      │
│  ✅  Response rate ≥ 90%         +5                       │
│  ✅  Community contributions     +5                       │
│                                                           │
│  NEGATIVE SIGNALS:                                        │
│  ⚠️   Open disputes              -15 each                 │
│  ⚠️   Received valid reports     -10 each                 │
│  ⚠️   Cancellation rate > 20%   -15                      │
│  ❌  Active suspension           -30                      │
│  ❌  Past ban                    permanent flag           │
│                                                           │
│  SCORE → PUBLIC BADGE:                                    │
│  90–100 → 🏆 "Top Seller"                                │
│  70–89  → ⭐ "Reliable Seller"                           │
│  50–69  → ✅ "Verified Member"                            │
│  0–49   → 🆕 "New Member"                                │
└──────────────────────────────────────────────────────────┘
```

### 8c. Appeal Flow

```
User (suspended)          FastAPI              Moderator
       │                     │                     │
       │  POST /reports/     │                     │
       │  {id}/appeal        │                     │
       │  {statement: "I     │                     │
       │   did not violate   │                     │
       │   any rules..."}    │                     │
       │────────────────────▶│                     │
       │                     │  INSERT appeal      │
       │                     │  Freeze case        │
       │  {appeal_id,        │  (can't re-moderate │
       │   status: pending}  │   while appealing)  │
       │◀────────────────────│                     │
       │                     │  🔔 Alert senior    │
       │                     │     moderator       │
       │                     │────────────────────▶│
       │                     │                     │  Senior reviews:
       │                     │                     │  • Original report
       │                     │                     │  • Evidence
       │                     │                     │  • User history
       │                     │                     │  • Appeal statement
       │                     │                     │
       │                     │                     │  UPHOLD or OVERTURN
       │                     │◀────────────────────│
       │                     │  UPDATE suspension  │
       │  🔔 Appeal decision  │  LOG audit_entry    │
       │◀────────────────────│                     │
```

---

## 9. Reviews & Reputation

### 9a. Review Flow

```
Transaction COMPLETED
      │
      ▼ (both buyer and seller see prompt in chat + notification)
      │
      ├── Buyer reviews Seller              ├── Seller reviews Buyer
      │                                     │
      │  POST /reviews                      │  POST /reviews
      │  {transaction_id,                   │  {transaction_id,
      │   review_type:                      │   review_type:
      │   "buyer_reviews_seller",           │   "seller_reviews_buyer",
      │   rating: 4,                        │   rating: 5,
      │   comment: "Fast response,          │   comment: "Great buyer,
      │   good condition",                  │   paid promptly",
      │   dimensions: [                     │   dimensions: [
      │     {dimension: "description_       │     {dimension: "communication",
      │      accuracy", rating: 4},         │      rating: 5},
      │     {dimension: "condition_         │     {dimension: "pickup_
      │      accuracy", rating: 3},         │      punctuality", rating: 5}
      │     {dimension: "communication",    │   ]}
      │      rating: 5},
      │     {dimension: "pickup_
      │      punctuality", rating: 4}
      │   ]}

Rules enforced by DB:
  ✅ UniqueConstraint(transaction_id, reviewer_user_id)
     → Each side reviews exactly once
  ✅ Transaction must have status=completed
  ✅ Reviewer must be buyer or seller of that transaction
  ✅ Both reviews held until both submit (or 14 days)

Display on profile:
  avg_rating = weighted avg of all review dimensions
  rating_count = total reviews received
  response_rate = (responses / total chat requests) * 100
  avg_response_time = median reply time in minutes
```

### 9b. Seller Reputation Dashboard

```
┌──────────────────────────────────────────────────────────┐
│  BookNook  ⭐ 4.7  (234 reviews)  ✅ Reliable Seller      │
│                                                           │
│  Description accuracy:  ████████░░  4.6 / 5              │
│  Condition accuracy:    ████████░░  4.5 / 5              │
│  Communication:         █████████░  4.8 / 5              │
│  Pickup punctuality:    █████████░  4.9 / 5              │
│                                                           │
│  📊 Stats:                                               │
│  Completed transactions:  234                            │
│  Cancellation rate:       2.1%                           │
│  Response rate:           98%                            │
│  Avg response time:       4 minutes                      │
│  Member since:            Jan 2025 (18 months)           │
│                                                           │
│  🏷️ Badges:                                               │
│  ✅ Email verified  📱 Phone verified  ⭐ Reliable Seller  │
└──────────────────────────────────────────────────────────┘
```

---

## 10. Community Flows

### 10a. Community Types & Visibility

```
┌──────────────────────────────────────────────────────────┐
│  Community Visibility Rules                               │
│                                                           │
│  PUBLIC    → Discoverable, anyone can join, posts public  │
│  PRIVATE   → Discoverable, join requires approval        │
│  SECRET    → Not discoverable, invite only               │
│  VERIFIED  → Requires institution email verification     │
│                                                           │
│  Community Types (discovery by):                         │
│  • College / University  • Genre / Author / Book         │
│  • City / Neighborhood   • Course / Exam                 │
│  • Workplace             • Language                      │
│  • Library / Bookstore   • Social cause                  │
└──────────────────────────────────────────────────────────┘
```

### 10b. Community Post Types & Feed

```
Member creates post:
  POST /communities/{id}/posts
  {type: "recommendation"|"text"|"poll"|"question"|
         "reading_update"|"listing"|"event"|"challenge",
   content: "Anyone have a good Economics textbook?",
   listing_id: null,
   poll_options: null}

Feed algorithm:
  GET /communities/{id}/feed?cursor=...
  → Pinned posts (by mods) first
  → Chronological for non-pinned
  → Cursor-based pagination (20 per page)

Post moderation actions (owner/mod):
  • Pin post
  • Remove post (with reason)
  • Slow mode (60s between posts per user)
  • Member mute (user can read but not post)
  • Member ban from community
```

### 10c. Community Marketplace Tab

```
GET /communities/{id}/marketplace
  → Returns active listings from community members
  → Filtered by community location/scope
  → "Buy within your community" feature
  → Members can see seller's role in community
  → Trust signal: "Member for 8 months"
```

---

## 11. Book Club Flows

### 11a. Book Club Full Lifecycle

```
Club Leader             Members              FastAPI
     │                     │                    │
     │  CREATE CLUB        │                    │
     │  POST /clubs        │                    │
     │  {name, community_  │                    │
     │   id, description,  │                    │
     │   reading_pace:     │                    │
     │   "1 chapter/week"} │                    │
     │────────────────────────────────────────▶│
     │                     │                    │
     │  NOMINATE BOOKS     │                    │
     │  POST /clubs/{id}/  │                    │
     │  nominations        │                    │
     │  {book_id}          │                    │
     │  (×3 nominations)   │                    │
     │────────────────────────────────────────▶│
     │                     │                    │
     │  VOTING PERIOD      │                    │
     │                     │  Each member votes  │
     │                     │  POST /clubs/{id}/  │
     │                     │  votes              │
     │                     │  {ranked_choices:   │
     │                     │   ["book_a",        │
     │                     │    "book_c",        │
     │                     │    "book_b"]}       │
     │                     │──────────────────────▶│
     │                     │                    │  Ranked-choice
     │                     │                    │  vote tallying
     │                     │                    │  (deterministic)
     │                     │                    │
     │  SELECT WINNER      │                    │
     │  POST /clubs/{id}/  │                    │
     │  club-books/select  │                    │
     │  {nomination_id:    │                    │
     │   "winning_book"}   │                    │
     │────────────────────────────────────────▶│
     │                     │                    │  🔔 All members:
     │                     │                    │  "New book selected:
     │                     │  🔔 Notification!   │   Atomic Habits"
     │                     │◀───────────────────│
     │                     │                    │
     │                     │                    │  Auto-link to
     │                     │                    │  marketplace:
     │                     │                    │  "12 copies available
     │                     │                    │   near members"
     │                     │                    │
     │  SET MILESTONES     │                    │
     │  POST /reading/     │                    │
     │  milestones         │                    │
     │  [{chapter: 5,      │                    │
     │    due_date,        │                    │
     │    discussion_topic}│                    │
     │   ×10 milestones]   │                    │
     │────────────────────────────────────────▶│
```

### 11b. Spoiler Protection System

```
Reader posts at chapter 12:
  POST /reading/milestones
  {content: "The twist in chapter 12 was insane!",
   spoiler_chapter: 12,
   spoiler_percentage: 40}

Other member at chapter 6 sees:
  ┌─────────────────────────────────────────────┐
  │  🔒 SPOILER — Chapter 12                    │
  │  You're at chapter 6.                       │
  │  [Reveal anyway]  [Skip]                    │
  └─────────────────────────────────────────────┘

Member at chapter 15 sees:
  Full content (no spoiler gate)

Progress-gated reveal logic:
  IF reader.current_chapter >= post.spoiler_chapter
    → show content
  ELSE
    → show spoiler warning
    → only reveal on explicit user tap
```

### 11c. Buddy Read & Readalong

```
BUDDY READ (small private group, 2-8 people):
  POST /buddy-reads
  {book_id, member_ids: ["a","b","c"],
   start_date, end_date}
  → Shared private space
  → See each other's progress bars
  → Page-gated discussions

READALONG (large group, unlimited):
  POST /readalongs
  {book_id, host_user_id, is_public: true,
   start_date, chapter_schedule}
  → Chapter rooms open on schedule
  → Host makes announcements
  → Progress milestones unlock discussions
```

---

## 12. Events Flow

### 12a. Event Lifecycle

```
Organizer               FastAPI               Attendees
    │                      │                       │
    │  POST /events        │                       │
    │  {title: "IISc       │                       │
    │   Book Exchange",    │                       │
    │   type: "book_       │                       │
    │   exchange",         │                       │
    │   starts_at:         │                       │
    │   "2026-08-15        │                       │
    │   10:00 IST",        │                       │
    │   location_label:    │                       │
    │   "IISc Main Gate",  │                       │
    │   lat: 13.02,        │                       │
    │   lng: 77.57,        │                       │
    │   capacity: 100,     │                       │
    │   community_id,      │                       │
    │   is_free: true}     │                       │
    │─────────────────────▶│                       │
    │  {event_id}          │                       │
    │◀─────────────────────│                       │
    │                      │                       │
    │                      │  GET /events?         │
    │                      │  lat=...&city=...     │
    │                      │◀──────────────────────│
    │                      │                       │
    │                      │  POST /events/{id}/   │
    │                      │  rsvp                 │
    │                      │  {status: "going"}    │
    │                      │◀──────────────────────│
    │                      │                       │
    │                      │  Capacity check:      │
    │                      │  IF going_count < cap │
    │                      │    → RSVP confirmed   │
    │                      │  ELSE                 │
    │                      │    → Waitlist entry   │
    │                      │                       │
    │  QR CHECK-IN         │                       │
    │  (day of event)      │                       │
    │  POST /events/{id}/  │                       │
    │  check-in            │                       │
    │  {attendee_user_id}  │                       │
    │─────────────────────▶│  INSERT event_checkin │
    │                      │  UPDATE attendance    │
    │  ✅ "Checked in!"     │  count                │
    │◀─────────────────────│                       │
    │                      │                       │
    │  GET /events/{id}/   │                       │
    │  calendar            │                       │
    │──────────────────────────────────────────────▶│
    │  Returns ICS file    │                       │  (Add to Google
    │  for calendar import │                       │   Calendar)
```

---

## 13. Reading Tracker

### 13a. Reading Progress Flow

```
User                         FastAPI                      Database
  │                              │                             │
  │  CREATE SHELF               │                             │
  │  POST /reading/shelves      │                             │
  │  {name: "Currently Reading",│                             │
  │   shelf_type: "reading",    │                             │
  │   is_public: true}          │                             │
  │─────────────────────────────▶                             │
  │                              │  INSERT reading_shelf      │
  │                              │─────────────────────────────▶│
  │                              │                             │
  │  ADD BOOK TO SHELF          │                             │
  │  POST /reading/shelves/     │                             │
  │  {id}/items                 │                             │
  │  {book_id: "b1",            │                             │
  │   start_date: "2026-07-01"} │                             │
  │─────────────────────────────▶                             │
  │                              │  INSERT shelf_item         │
  │                              │─────────────────────────────▶│
  │                              │                             │
  │  UPDATE PROGRESS (daily)    │                             │
  │  PUT /reading/progress      │                             │
  │  {shelf_item_id: "si1",     │                             │
  │   current_page: 142,        │                             │
  │   total_pages: 320,         │                             │
  │   reading_time_minutes: 45} │                             │
  │─────────────────────────────▶                             │
  │                              │  UPSERT reading_progress   │
  │                              │  (idempotent: same page =  │
  │                              │   no new record)           │
  │  {progress_pct: 44.4%}      │  UPDATE statistics         │
  │◀─────────────────────────────│─────────────────────────────▶│
  │                              │                             │
  │  ADD READING NOTE           │                             │
  │  POST /reading/notes        │                             │
  │  {shelf_item_id: "si1",     │                             │
  │   note_type: "highlight"|   │                             │
  │   "thought"|"question",     │                             │
  │   content: "Great analogy   │                             │
  │   on page 142",             │                             │
  │   page_number: 142,         │                             │
  │   is_private: true}         │                             │
  │─────────────────────────────▶                             │
  │  {note_id}                  │  INSERT reading_note       │
  │◀─────────────────────────────│─────────────────────────────▶│
```

### 13b. Reading Goals & Statistics

```
GOAL TYPES:
  POST /reading/goals
  {type: "books_per_year",    target: 24, year: 2026}
  {type: "pages_per_month",   target: 500, month: 7, year: 2026}
  {type: "minutes_per_day",   target: 30}
  {type: "genre_challenge",   target: 5, genre: "science"}
  {type: "community_challenge", challenge_id: "ch1"}

STATISTICS (recomputed on demand):
  POST /reading/statistics/recompute
  →  {books_completed: 7,
      pages_read: 2341,
      reading_streak: 14,  ← consecutive days with progress
      avg_pages_per_day: 32,
      total_reading_time_hours: 45,
      top_genres: ["Science","History","Fiction"],
      books_by_month: {Jan:2, Feb:1, Mar:3,...},
      money_saved: ₹2800  ← vs buying new
      books_exchanged: 4,
      books_donated: 2}

YEAR SUMMARY (auto-generated Dec 31):
  "In 2026, you read 24 books, 7,234 pages,
   saved ₹8,400 vs new prices, exchanged
   12 books with 8 different readers!"
```

---

## 14. Institution & Donation

### 14a. Institution Onboarding

```
Institution Admin                    FastAPI                Platform Admin
        │                               │                         │
        │  POST /institutions           │                         │
        │  {name: "IISc Bangalore",     │                         │
        │   type: "university",         │                         │
        │   description: "...",         │                         │
        │   website: "iisc.ac.in",      │                         │
        │   city: "Bangalore",          │                         │
        │   state: "Karnataka"}         │                         │
        │──────────────────────────────▶│                         │
        │  {id, status: "pending",      │                         │
        │   slug: "iisc-bangalore"}     │                         │
        │◀──────────────────────────────│                         │
        │                               │                         │
        │  POST /institutions/          │                         │
        │  {id}/domains                 │                         │
        │  {domain: "iisc.ac.in"}       │                         │
        │──────────────────────────────▶│                         │
        │  {domain_id, verified: false} │                         │
        │◀──────────────────────────────│                         │
        │                               │                         │
        │                               │  Platform admin verifies│
        │                               │  domain ownership (DNS) │
        │                               │  POST /institutions/    │
        │                               │  {id}/verify            │
        │                               │◀────────────────────────│
        │                               │  UPDATE institution     │
        │                               │  is_verified=true       │
        │                               │  UPDATE domain          │
        │  🔔 Institution verified!     │  is_verified=true       │
        │◀──────────────────────────────│                         │
        │                               │                         │
        │  Students with @iisc.ac.in    │                         │
        │  email can now auto-join:     │                         │
        │                               │                         │
        │  POST /institutions/{id}/join │                         │
        │  {role: "student"}            │                         │
        │  → Check email domain match  │                         │
        │  → Auto-approve if verified  │                         │
```

### 14b. Donation Campaign Complete Flow

```
Campaign Creator (NGO/Library)        Donor                     Recipient
           │                            │                           │
           │  CREATE CAMPAIGN           │                           │
           │  POST /donations/campaigns │                           │
           │  {title: "Books for Rural  │                           │
           │   Schools in Karnataka",   │                           │
           │   institution_id: "ngo1",  │                           │
           │   needs: [                 │                           │
           │    {title: "English        │                           │
           │     Reader Grade 5",       │                           │
           │     qty_needed: 20},       │                           │
           │    {title: "Math Class 6", │                           │
           │     qty_needed: 15}],      │                           │
           │   quantity_target: 35,     │                           │
           │   deadline: "2026-09-30",  │                           │
           │   pickup_address: "NGO HQ, │                           │
           │   Jayanagar"}              │                           │
           │────────────────────────────────────────────────────────▶
           │                            │                           │
           │  PUBLISH CAMPAIGN          │                           │
           │  POST .../publish          │                           │
           │────────────────────────────────────────────────────────▶
           │                            │                           │
           │                            │  Browse campaigns         │
           │                            │  GET /donations/          │
           │                            │  campaigns?city=Bangalore │
           │                            │─────────────────────────────▶
           │                            │                           │
           │                            │  PLEDGE BOOKS             │
           │                            │  POST .../pledge          │
           │                            │  {donation_need_id: "n1", │
           │                            │   title_snapshot:         │
           │                            │   "English Reader Gr.5",  │
           │                            │   condition: "good",      │
           │                            │   quantity: 3,            │
           │                            │   notes: "Lightly used"}  │
           │                            │─────────────────────────────▶
           │                            │  🔔 New pledge!           │
           │  ◀─────────────────────────────────────────────────────│
           │                            │                           │
           │  ACCEPT PLEDGE             │                           │
           │  POST .../accept           │                           │
           │────────────────────────────────────────────────────────▶
           │  🔔 Pledge accepted!        │                           │
           │  "Drop off at NGO HQ       │                           │
           │   anytime this week"       │                           │
           │──────────────────────────────▶                         │
           │                            │                           │
           │  MARK RECEIVED             │                           │
           │  POST .../received         │                           │
           │────────────────────────────────────────────────────────▶
           │                            │                           │
           │  ISSUE RECEIPT             │                           │
           │  POST .../receipt          │                           │
           │  {receipt_text: "Thank you │                           │
           │   for donating 3 books",   │                           │
           │   impact_note: "These books│                           │
           │   will reach Kolar         │                           │
           │   district students"}      │                           │
           │────────────────────────────────────────────────────────▶
           │                            │  🔔 Receipt received!     │
           │                            │◀──────────────────────────│
```

---

## 15. Professional Seller

### 15a. Business Profile Setup

```
Professional Seller                  FastAPI
        │                               │
        │  CREATE PROFILE               │
        │  POST /business               │
        │  {name: "BookNook Store",     │
        │   type: "shop",               │
        │   description: "Second-hand   │
        │   academic books since 2020", │
        │   website: "booknook.in",     │
        │   gstin: "29ABCDE1234F1Z5"}   │
        │──────────────────────────────▶│
        │  {id, slug: "booknook-store", │
        │   status: "pending"}          │
        │◀──────────────────────────────│
        │                               │
        │  ADD LOCATIONS                │
        │  POST /business/{id}/         │
        │  locations                    │
        │  {name: "Jayanagar Branch",   │
        │   address: "12 11th Main",    │
        │   city: "Bangalore",          │
        │   is_primary: true}           │
        │──────────────────────────────▶│
        │                               │
        │  INVITE STAFF                 │
        │  POST /business/{id}/staff    │
        │  {user_id: "staff1",          │
        │   role: "manager"}            │
        │──────────────────────────────▶│
        │                               │  🔔 Staff notified
        │                               │
        │  BULK IMPORT                  │
        │  POST /business/{id}/imports  │
        │  {filename: "inventory.csv"}  │
        │──────────────────────────────▶│
        │  {import_id,                  │  Worker picks up:
        │   status: "pending"}          │  • Parse CSV
        │◀──────────────────────────────│  • Resolve ISBNs
        │                               │  • Create listings
        │  GET .../imports/{id}         │  • Report errors
        │  {status: "completed",        │
        │   total: 500, success: 487,   │
        │   errors: 13}                 │
```

### 15b. Subscription Plans

```
┌──────────────────────────────────────────────────────────────┐
│                    SUBSCRIPTION PLANS                         │
│                                                               │
│  FREE (₹0/mo)          PLUS (₹199/mo)      PRO (₹599/mo)    │
│  ─────────────         ──────────────      ────────────────  │
│  10 listings           50 listings         500 listings       │
│  3 saved searches      20 saved searches   Unlimited          │
│  1 community           5 communities       20 communities     │
│  Basic alerts          Instant alerts      Priority alerts    │
│                        Ad-free             Ad-free            │
│                        Advanced stats      Full analytics     │
│                        Early access        Staff accounts     │
│                        listings            Bulk import        │
│                                            Promotions         │
│                                            API access         │
│                                            Priority support   │
│                                                               │
│  POST /subscriptions  {plan_id: "plus"}                       │
│  → Local provider (dev) or Razorpay (prod)                    │
│  → Subscription active immediately                            │
│  → Entitlements enforced in service layer                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 16. Recommendations & AI

### 16a. Recommendation Engine Flow

```
                    ┌────────────────────────────────────────┐
                    │       RECOMMENDATION ENGINE             │
                    │          (Rule-Based)                   │
                    └──────────────────┬─────────────────────┘
                                       │
                    ┌──────────────────▼─────────────────────┐
                    │           SIGNAL GATHERING              │
                    │                                         │
                    │  Signal 1: WISHLIST                     │
                    │  → Query: books in user wishlist        │
                    │  → Find: active listings for those books│
                    │  → Score: 0.95 (highest intent)        │
                    │                                         │
                    │  Signal 2: READING HISTORY (Genre)      │
                    │  → Query: user's completed books        │
                    │  → Extract: top 3 genres                │
                    │  → Find: new listings in those genres   │
                    │  → Score: 0.70                         │
                    │                                         │
                    │  Signal 3: COMMUNITY                    │
                    │  → Query: current club books            │
                    │  → Find: available copies near members  │
                    │  → Score: 0.80                         │
                    │                                         │
                    │  Signal 4: LOCATION                     │
                    │  → Query: listings within 5km           │
                    │  → Filter: added in last 48h            │
                    │  → Score: 0.60                         │
                    │                                         │
                    │  Signal 5: TRENDING                     │
                    │  → Query: most-saved listings, 7 days   │
                    │  → Filter: user hasn't seen             │
                    │  → Score: 0.50                         │
                    └──────────────────┬─────────────────────┘
                                       │
                    ┌──────────────────▼─────────────────────┐
                    │    MERGE, DEDUPLICATE, SORT BY SCORE    │
                    └──────────────────┬─────────────────────┘
                                       │
                    ┌──────────────────▼─────────────────────┐
                    │     SAVE TO recommendations TABLE       │
                    │     (refreshed every 24h per user)      │
                    └──────────────────┬─────────────────────┘
                                       │
                                       ▼
        GET /recommendations
        Response:
        [{entity_type: "listing", entity_id: "l1",
          score: 0.95, reason: "In your wishlist",
          source: "wishlist"},
         {entity_type: "listing", entity_id: "l2",
          score: 0.80, reason: "Your book club is reading Dune",
          source: "community"},
         ...]

User interactions:
  POST /recommendations/{id}/click    → track engagement
  POST /recommendations/{id}/dismiss  → never show again
  POST /recommendations/{id}/feedback
       {type: "not_interested"|"already_have"|"helpful"}
```

### 16b. Price Suggestion

```
GET /recommendations/price-suggestion?book_id=xyz&condition=good

Logic:
  1. Find all active listings for same book
  2. Filter by condition range (good ± 1 level)
  3. Calculate: avg, p25, p75
  4. Apply condition multiplier:
     new_sealed=1.0, like_new=0.85, excellent=0.70,
     very_good=0.55, good=0.45, acceptable=0.30

Response:
  {suggested_cents: 35000,  ← ₹350
   min_cents: 25000,
   max_cents: 45000,
   basis: "Average of 8 similar active listings",
   condition_used: "good",
   comparable_count: 8}
```

### 16c. Category Suggestions

```
GET /recommendations/category-suggestions
    ?title=Physics+Part+II&description=NCERT+Class+12

Logic (keyword matching):
  title/description → keyword extract →
  match against category slugs + keywords →
  return top 3 matches

Response:
  [{slug: "science/physics", confidence: 0.95},
   {slug: "academic/class-12", confidence: 0.90},
   {slug: "academic/ncert", confidence: 0.85}]
```

---

## 17. Notifications

### 17a. Notification Delivery Pipeline

```
Domain Event               Transactional Outbox           Worker Process
     │                           │                               │
     │  (Any side effect:        │                               │
     │   offer accepted,         │                               │
     │   message received,       │                               │
     │   order shipped, etc.)    │                               │
     │                           │                               │
     │  BEGIN TRANSACTION        │                               │
     │  INSERT domain change     │                               │
     │  INSERT outbox_event      │                               │
     │  COMMIT                   │                               │
     │──────────────────────────▶│                               │
     │                           │  Worker polls outbox          │
     │                           │  every 5 seconds              │
     │                           │◀──────────────────────────────│
     │                           │                               │
     │                           │  For each unprocessed event:  │
     │                           │  1. Check user preferences    │
     │                           │  2. Check quiet hours         │
     │                           │  3. Check digest setting      │
     │                           │──────────────────────────────▶│
     │                           │                               │
     │                           │  IN-APP: INSERT notification  │
     │                           │  (always, unless muted)       │
     │                           │──────────────────────────────▶
     │                           │                               │
     │                           │  EMAIL: Send if enabled       │
     │                           │  (template + variables)       │
     │                           │──────────────────────────────▶
     │                           │                               │
     │                           │  PUSH: FCM/APNS if enabled    │
     │                           │──────────────────────────────▶
     │                           │                               │
     │                           │  SMS: Critical only           │
     │                           │  (payment, security alerts)   │
     │                           │──────────────────────────────▶
     │                           │                               │
     │                           │  Mark outbox event processed  │
     │                           │──────────────────────────────▶
```

### 17b. Notification Types Reference

```
┌────────────────────────────────────────────────────────────┐
│  NOTIFICATION TYPE          CHANNEL       PRIORITY          │
├────────────────────────────────────────────────────────────┤
│  Chat request received      In-app+Push   Medium           │
│  Message received           In-app+Push   Medium           │
│  Offer made on listing      In-app+Push   High             │
│  Offer accepted             In-app+Push   High             │
│  Counteroffer received      In-app+Push   High             │
│  Order payment confirmed    In-app+Email  High             │
│  Seller accepted order      In-app+Push   High             │
│  Shipment dispatched        In-app+Email  Medium           │
│  Order delivered            In-app+Email  Medium           │
│  Transaction completed      In-app+Email  Medium           │
│  Review received            In-app        Low              │
│  Wishlist match (new copy)  In-app+Push   Medium           │
│  Saved search match         In-app        Low              │
│  Nearby listing             In-app        Low              │
│  Price drop alert           In-app+Push   Medium           │
│  Community post             In-app        Low              │
│  Mention (@username)        In-app+Push   High             │
│  Event reminder (24h)       In-app+Push   Medium           │
│  Reading goal reminder      In-app        Low              │
│  ⚠️  Suspicious login         In-app+Email+SMS Critical    │
│  Account suspended          In-app+Email  Critical         │
│  Refund processed           In-app+Email  High             │
│  Dispute update             In-app+Email  High             │
└────────────────────────────────────────────────────────────┘

User Preferences (PATCH /notification-preferences):
  {
    chat_request: {in_app: true, push: true, email: false},
    message: {in_app: true, push: true, email: false},
    offer: {in_app: true, push: true, email: true},
    order: {in_app: true, push: true, email: true},
    quiet_hours: {enabled: true, from: "22:00", to: "08:00"},
    digest: "immediate" | "daily" | "weekly"
  }
```

---

## 18. Admin & Moderation

### 18a. Admin Dashboard & Tools

```
┌──────────────────────────────────────────────────────────────────┐
│                       ADMIN APP (port 3001)                       │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  DASHBOARD  │  │    USERS    │  │  LISTINGS   │             │
│  │             │  │             │  │             │             │
│  │ Total users │  │ Search by   │  │ Filter by   │             │
│  │ Active list.│  │ email/name  │  │ status/flag │             │
│  │ Open reports│  │ Filter:     │  │ Actions:    │             │
│  │ Pending mod │  │ verified/   │  │ approve     │             │
│  │ Revenue KPI │  │ suspended   │  │ suspend     │             │
│  │ Disputes    │  │ Actions:    │  │ remove      │             │
│  └─────────────┘  │ warn        │  └─────────────┘             │
│                   │ suspend Nd  │                               │
│  ┌─────────────┐  │ ban perm    │  ┌─────────────┐             │
│  │   REPORTS   │  │ unsuspend   │  │  MODERATION │             │
│  │   QUEUE     │  └─────────────┘  │   CASES     │             │
│  │             │                   │             │             │
│  │ Filter by:  │  ┌─────────────┐  │ Cases from  │             │
│  │ type        │  │  PAYMENTS   │  │ escalated   │             │
│  │ severity    │  │             │  │ reports     │             │
│  │ status      │  │ Orders      │  │ Assign to   │             │
│  │             │  │ Payments    │  │ moderator   │             │
│  │ Bulk:       │  │ Payouts     │  │ Priority    │             │
│  │ reviewing   │  │ Refunds     │  │ color code  │             │
│  │ assign self │  │ Disputes    │  │             │             │
│  │             │  │ → Resolve   │  │ Action:     │             │
│  │ Click →     │  │   buyer/    │  │ warn        │             │
│  │ Report      │  │   seller    │  │ remove      │             │
│  │ Detail      │  └─────────────┘  │ suspend     │             │
│  └─────────────┘                   │ ban         │             │
│                                    └─────────────┘             │
│                                                                   │
│  ANALYTICS   COMMUNITIES   SUBSCRIPTIONS   AUDIT LOGS            │
└──────────────────────────────────────────────────────────────────┘
```

### 18b. Moderation Decision Tree

```
Report received
      │
      ▼
Auto-classify severity
      │
      ├── CRITICAL (child safety, doxxing)
      │   → Immediately restrict content
      │   → Alert senior moderator
      │   → 2h SLA
      │
      ├── HIGH (harassment, fraud, copyright)
      │   → Queue to priority lane
      │   → 24h SLA
      │
      ├── MEDIUM (fake listing, misleading)
      │   → Standard queue
      │   → 72h SLA
      │
      └── LOW (spam, off-topic)
          → Auto-handle if repeat pattern
          → 1 week SLA

Moderator Reviews Case:
  → See: reporter, target, reason, evidence
  → See: reporter history, target history
  → See: related reports for same user

Decision:
  DISMISS         → Log, close case
  WARN            → Send warning to user, log audit
  REMOVE CONTENT  → Delete/hide content, log audit
  SUSPEND (Nd)    → Block access N days, log audit
  BAN             → Permanent block, log audit

All actions → INSERT audit_log
  {actor_id, action, target_id, reason,
   case_id, timestamp}

User notified of:
  warn, suspend, ban → email + in-app
  User can appeal → POST /reports/{id}/appeal
```

---

## 19. Complete User Journey

### 19a. Buyer Journey (A to Z)

```
DISCOVER
    │
    ├── Google search → Land on listing
    │   or
    ├── Browse /communities → See post → Click listing
    │   or
    └── Get recommendation → Click from /dashboard

EVALUATE
    │
    ├── View listing detail (photos, condition, price)
    ├── Check seller profile (rating, verified badges)
    ├── View "Similar copies" from other sellers
    └── Check approximate location on map

CONNECT
    │
    ├── Click "Message Seller" → Send chat request
    ├── Seller accepts → Conversation opens
    └── Chat about condition, price, pickup

NEGOTIATE
    │
    ├── Make price offer (₹350 → Seller counters ₹380)
    └── Accept counteroffer

TRANSACT
    │
    ├── Cash pickup path:
    │   └── Propose pickup time/location
    │       → Confirm → Get handover code
    │       → Meet → Exchange books + code
    │       → Mark complete
    │
    └── Online payment path:
        └── Cart → Checkout → Pay via UPI/card
            → Seller ships → Track delivery
            → Confirm received

REVIEW
    │
    └── Leave review for seller (dimensions rated)
        Seller leaves review for buyer

REPEAT
    │
    ├── Add more books to wishlist
    ├── Follow this seller
    ├── Join their reading community
    └── List your own books to sell!
```

### 19b. Seller Journey (A to Z)

```
SETUP
    │
    ├── Register + Verify email
    ├── Complete profile (bio, location, languages)
    └── Optional: Create business profile

LIST
    │
    ├── Scan ISBN or search title
    ├── Fill condition details (honest!)
    ├── Set price (use AI price suggestion)
    ├── Upload actual photos (quality score tips)
    └── Publish listing

MANAGE INQUIRIES
    │
    ├── Receive chat requests → Accept genuine buyers
    ├── Respond quickly (better response rate = higher rank)
    ├── Evaluate offers → Accept / Counter / Decline
    └── Block suspicious users

COMPLETE SALE
    │
    ├── Accept offer → Transaction created
    ├── Propose pickup or prepare shipment
    └── Handover book → Get code confirmed

GROW
    │
    ├── Build rating (aim for 4.5+ avg)
    ├── Earn "Reliable Seller" badge
    ├── Unlock Seller Pro for bulk tools
    ├── Run promotions for visibility
    └── Create business storefront
```

### 19c. Community Member Journey

```
DISCOVER
    │
    └── Browse /communities by location/genre/college

JOIN
    │
    ├── Public: Join instantly
    ├── Private: Request + await approval
    └── Verified: Prove institution email

ENGAGE
    │
    ├── Post reading updates, questions, recommendations
    ├── React to posts (👍❤️📚)
    ├── Comment and discuss
    ├── Participate in polls
    └── Share listings in community marketplace

BOOK CLUB
    │
    ├── Nominate books
    ├── Vote (ranked-choice)
    ├── Read together with milestone discussions
    ├── Spoiler-protected chapter rooms
    └── Buddy read with small group

EVENTS
    │
    ├── RSVP to local book fairs / exchanges
    ├── QR check-in on arrival
    ├── Meet fellow readers in person
    └── Organize your own event
```

---

## 20. API Endpoint Reference

### Authentication & Identity
```
POST   /api/v1/auth/register            Register new user
POST   /api/v1/auth/login               Login with email/password
POST   /api/v1/auth/refresh             Refresh access token
POST   /api/v1/auth/logout              Logout current session
POST   /api/v1/auth/logout-all          Revoke all sessions
POST   /api/v1/auth/verify-email        Verify email token
POST   /api/v1/auth/forgot-password     Request password reset
POST   /api/v1/auth/reset-password      Reset password with token
GET    /api/v1/users/me                 Get own profile
PATCH  /api/v1/users/me                 Update own profile
GET    /api/v1/users/{id}               Get public profile
POST   /api/v1/users/{id}/block         Block user
DELETE /api/v1/users/{id}/block         Unblock user
GET    /api/v1/users/me/sessions        List active sessions
DELETE /api/v1/users/me/sessions/{id}   Revoke session
```

### Catalog
```
GET    /api/v1/books                    List/search books
GET    /api/v1/books/{id}               Get book detail
POST   /api/v1/books                    Create book entry (auth)
POST   /api/v1/books/resolve-isbn       Lookup book by ISBN
GET    /api/v1/categories               Get category tree
GET    /api/v1/authors                  List authors
GET    /api/v1/publishers               List publishers
```

### Listings & Media
```
POST   /api/v1/listings                 Create listing
GET    /api/v1/listings/{id}            Get listing
PATCH  /api/v1/listings/{id}            Update listing
POST   /api/v1/listings/{id}/publish    Publish listing
POST   /api/v1/listings/{id}/pause      Pause listing
POST   /api/v1/listings/{id}/relist     Relist listing
DELETE /api/v1/listings/{id}            Delete listing
POST   /api/v1/media/upload-url         Get upload URL
POST   /api/v1/media/{id}/complete      Mark upload complete
```

### Search & Discovery
```
GET    /api/v1/search/listings          Search listings
GET    /api/v1/search/suggestions       Autocomplete suggestions
POST   /api/v1/saved-searches           Save search
GET    /api/v1/saved-searches           List saved searches
POST   /api/v1/wishlists/{book_id}      Add to wishlist
DELETE /api/v1/wishlists/{book_id}      Remove from wishlist
POST   /api/v1/listings/{id}/favorite   Favorite listing
DELETE /api/v1/listings/{id}/favorite   Unfavorite listing
POST   /api/v1/follows                  Follow user/seller
DELETE /api/v1/follows/{id}             Unfollow
```

### Chat & Notifications
```
POST   /api/v1/chat-requests            Send chat request
GET    /api/v1/chat-requests            List chat requests
POST   /api/v1/chat-requests/{id}/accept    Accept request
POST   /api/v1/chat-requests/{id}/decline   Decline request
POST   /api/v1/chat-requests/{id}/block     Block request
GET    /api/v1/conversations            List conversations
GET    /api/v1/conversations/{id}/messages  Get messages
POST   /api/v1/conversations/{id}/messages  Send message
WS     /ws/conversations?token=...      Real-time messages
GET    /api/v1/notifications            List notifications
PATCH  /api/v1/notifications/{id}       Mark read
GET    /api/v1/notification-preferences Get preferences
PATCH  /api/v1/notification-preferences Update preferences
```

### Commerce (Offers & Transactions)
```
POST   /api/v1/offers                   Make offer
GET    /api/v1/offers                   List offers (buyer/seller)
POST   /api/v1/offers/{id}/counter      Counter offer
POST   /api/v1/offers/{id}/accept       Accept offer
POST   /api/v1/offers/{id}/reject       Reject offer
POST   /api/v1/offers/{id}/withdraw     Withdraw offer
POST   /api/v1/pickups                  Propose pickup
POST   /api/v1/pickups/{id}/confirm     Confirm pickup
GET    /api/v1/orders                   List transactions
GET    /api/v1/orders/{id}              Get transaction
POST   /api/v1/transactions/{id}/complete Complete transaction
POST   /api/v1/reviews                  Leave review
```

### Payments & Shipping
```
POST   /api/v1/carts                    Create cart
GET    /api/v1/carts/{id}               Get cart
POST   /api/v1/carts/{id}/items         Add item to cart
DELETE /api/v1/carts/{id}/items/{iid}   Remove cart item
POST   /api/v1/carts/{id}/checkout      Checkout cart → order
GET    /api/v1/orders                   List orders
GET    /api/v1/orders/{id}              Get order
POST   /api/v1/orders/{id}/accept       Seller accepts order
POST   /api/v1/orders/{id}/cancel       Cancel order
POST   /api/v1/payments/{id}/initiate   Initiate payment
POST   /api/v1/payments/webhook/{prov}  Payment webhook
POST   /api/v1/shipments                Create shipment
GET    /api/v1/shipments/{id}           Get shipment
POST   /api/v1/shipments/webhook/{prov} Shipping webhook
POST   /api/v1/disputes                 Open dispute
GET    /api/v1/disputes/{id}            Get dispute
POST   /api/v1/disputes/{id}/evidence   Add evidence
POST   /api/v1/disputes/{id}/resolve    Resolve dispute
```

### Trust & Moderation
```
POST   /api/v1/reports                  Submit report
POST   /api/v1/reports/{id}/appeal      Appeal decision
GET    /api/v1/admin/moderation/cases   List mod cases
GET    /api/v1/admin/moderation/cases/{id}  Case detail
POST   /api/v1/admin/moderation/cases/{id}/action  Take action
GET    /api/v1/admin/users/{id}         Admin user view
GET    /api/v1/admin/listings/{id}      Admin listing view
GET    /api/v1/admin/conversations/{id}/evidence  Chat evidence
```

### Communities
```
POST   /api/v1/communities              Create community
GET    /api/v1/communities              Discover communities
GET    /api/v1/communities/{id}         Get community
POST   /api/v1/communities/{id}/join    Join community
POST   /api/v1/communities/{id}/approve-member  Approve member
POST   /api/v1/communities/{id}/posts   Create post
GET    /api/v1/communities/{id}/feed    Get feed
GET    /api/v1/communities/{id}/marketplace Community marketplace
POST   /api/v1/posts/{id}/comments     Comment on post
POST   /api/v1/posts/{id}/reactions    React to post
```

### Book Clubs & Events
```
POST   /api/v1/clubs                    Create book club
GET    /api/v1/clubs                    List clubs
GET    /api/v1/clubs/{id}               Get club
POST   /api/v1/clubs/{id}/books         Add club book
POST   /api/v1/clubs/{id}/nominations   Nominate book
POST   /api/v1/clubs/{id}/votes         Vote on nominations
POST   /api/v1/clubs/{id}/books/select  Select winning book
POST   /api/v1/events                   Create event
GET    /api/v1/events                   List events
GET    /api/v1/events/{id}              Get event
PATCH  /api/v1/events/{id}              Update event
POST   /api/v1/events/{id}/rsvp         RSVP to event
DELETE /api/v1/events/{id}/rsvp         Cancel RSVP
POST   /api/v1/events/{id}/check-in     Check in attendee
GET    /api/v1/events/{id}/calendar     ICS calendar export
POST   /api/v1/buddy-reads              Create buddy read
POST   /api/v1/buddy-reads/{id}/join    Join buddy read
POST   /api/v1/reading/milestones       Create milestone
```

### Reading Tracker
```
POST   /api/v1/reading/shelves          Create shelf
GET    /api/v1/reading/shelves/me       List my shelves
GET    /api/v1/reading/shelves/{uid}    List user shelves
POST   /api/v1/reading/shelves/{id}/items  Add to shelf
DELETE /api/v1/reading/shelves/{id}/items/{iid} Remove from shelf
PUT    /api/v1/reading/progress         Update progress
GET    /api/v1/reading/progress         List progress
POST   /api/v1/reading/notes            Create note
GET    /api/v1/reading/notes            List notes
POST   /api/v1/reading/goals            Create reading goal
GET    /api/v1/reading/goals            List goals
GET    /api/v1/reading/statistics       Get statistics
POST   /api/v1/reading/statistics/recompute  Recompute stats
```

### Institutions & Donations
```
POST   /api/v1/institutions             Create institution
GET    /api/v1/institutions             List institutions
GET    /api/v1/institutions/{id}        Get institution
PATCH  /api/v1/institutions/{id}        Update institution
POST   /api/v1/institutions/{id}/join   Join institution
GET    /api/v1/institutions/{id}/members List members
POST   /api/v1/institutions/{id}/approve-member  Approve member
POST   /api/v1/institutions/{id}/domains Add domain
POST   /api/v1/institutions/{id}/verify Verify institution
POST   /api/v1/donations/campaigns      Create campaign
GET    /api/v1/donations/campaigns      List campaigns
GET    /api/v1/donations/campaigns/{id} Get campaign
PATCH  /api/v1/donations/campaigns/{id} Update campaign
POST   /api/v1/donations/campaigns/{id}/publish  Publish
POST   /api/v1/donations/campaigns/{id}/pledge   Pledge books
GET    /api/v1/donations/campaigns/{id}/pledges  List pledges
POST   /api/v1/donations/campaigns/{id}/pledges/{pid}/accept   Accept
POST   /api/v1/donations/campaigns/{id}/pledges/{pid}/received Received
POST   /api/v1/donations/campaigns/{id}/pledges/{pid}/receipt  Issue receipt
GET    /api/v1/donations/pledges/me     My pledges
```

### Business & Subscriptions
```
POST   /api/v1/business                 Create business profile
GET    /api/v1/business                 List profiles
GET    /api/v1/business/{id}            Get profile
PATCH  /api/v1/business/{id}            Update profile
POST   /api/v1/business/{id}/locations  Add location
DELETE /api/v1/business/{id}/locations/{lid} Remove location
GET    /api/v1/business/{id}/staff      List staff
POST   /api/v1/business/{id}/staff      Invite staff
DELETE /api/v1/business/{id}/staff/{uid} Remove staff
POST   /api/v1/business/{id}/imports    Start import
GET    /api/v1/business/{id}/imports/{iid} Import status
GET    /api/v1/subscription-plans       List plans
POST   /api/v1/subscriptions            Subscribe
GET    /api/v1/subscriptions/me         My subscription
DELETE /api/v1/subscriptions/{id}       Cancel subscription
POST   /api/v1/promotions              Create promotion
GET    /api/v1/promotions/me           My promotions
DELETE /api/v1/promotions/{id}         Cancel promotion
POST   /api/v1/coupons                 Create coupon (admin)
GET    /api/v1/coupons                 List coupons
POST   /api/v1/coupons/validate        Validate coupon
```

### Recommendations
```
GET    /api/v1/recommendations                     My recommendations
POST   /api/v1/recommendations/refresh             Trigger refresh
POST   /api/v1/recommendations/{id}/click          Record click
POST   /api/v1/recommendations/{id}/dismiss        Dismiss
POST   /api/v1/recommendations/{id}/feedback       Submit feedback
GET    /api/v1/recommendations/price-suggestion    Price suggestion
GET    /api/v1/recommendations/category-suggestions Category suggestions
GET    /api/v1/listings/{id}/similar               Similar listings
```

### Health
```
GET    /health/live     Liveness probe (is API running?)
GET    /health/ready    Readiness probe (DB + Redis connected?)
```

---

## 21. Database Entity Map

```
IDENTITY (9 tables)
  users ──┬── user_profiles
          ├── user_sessions
          ├── user_devices
          ├── social_accounts
          ├── user_verifications
          ├── user_preferences
          ├── user_blocks
          └── consents

CATALOG (9 tables)
  books ──┬── book_editions
          ├── book_authors ── authors
          ├── book_categories ── categories (tree)
          ├── book_identifiers (ISBN etc.)
          ├── academic_metadata
          └── publishers

MARKETPLACE (8 tables)
  listings ──┬── listing_conditions
             ├── listing_locations (PostGIS)
             ├── listing_delivery_methods
             ├── listing_price_history
             ├── listing_inventory
             └── media_assets

DISCOVERY (5 tables)
  saved_searches · wishlists · follows
  listing_favorites · zero_result_searches

COMMUNICATION (8 tables)
  chat_requests ── conversations ──┬── conversation_members
                                   ├── messages ──┬── message_attachments
                                                  └── message_reads

NOTIFICATIONS (3 tables)
  notifications · notification_preferences · notification_deliveries

COMMERCE (6 tables)
  offers ──┬── exchange_offer_items
           └── transactions ──┬── pickup_sessions
                              └── reviews ── review_dimensions

PAYMENTS (10 tables)
  carts ── cart_items
  orders ── order_items
  payments · payouts · refunds
  shipments · disputes
  webhook_events · idempotency_keys

TRUST (6 tables)
  reports · moderation_cases · moderation_actions
  risk_events · device_risk · audit_logs

COMMUNITIES (9 tables)
  communities ──┬── community_members
               ├── community_roles
               ├── community_rules
               ├── community_channels
               ├── community_posts ──┬── post_comments
               │                    └── post_reactions
               └── community_reports

READING (6 tables)
  shelves ── shelf_items ── reading_progress
  reading_notes · reading_goals · reading_statistics

CLUBS & EVENTS (10 tables)
  book_clubs ──┬── club_books
               ├── book_nominations ── book_votes
               └── reading_milestones
  buddy_reads · readalongs
  events ──┬── event_rsvps
           ├── event_waitlists
           └── event_checkins

INSTITUTIONS (3 tables)
  institutions ──┬── institution_domains
                 └── institution_members

DONATIONS (4 tables)
  donation_campaigns ──┬── donation_needs
                       └── donation_pledges ── donation_receipts

MONETIZATION (8 tables)
  business_profiles ──┬── business_locations
                      ├── staff_accounts
                      └── inventory_imports
  subscription_plans ── subscriptions
  promotions · coupons

RECOMMENDATIONS (2 tables)
  recommendations · recommendation_feedbacks
```

---

## 22. Scope Summary

### Features by Milestone

| Milestone | Name | Status | Migrations |
|---|---|---|---|
| M0 | Foundation (monorepo, Docker, CI) | ✅ Done | 0001 |
| M1 | Identity & Profiles | ✅ Done | 0002 |
| M2 | Book Catalog | ✅ Done | 0003 |
| M3 | Listings & Media | ✅ Done | 0004 |
| M4 | Search & Discovery | ✅ Done | 0005 |
| M5 | Chat & Notifications | ✅ Done | 0006 |
| M6 | Offers, Pickup & Reviews | ✅ Done | 0007 |
| M7 | Trust, Reports & Moderation | ✅ Done | 0008 |
| M8 | Communities | ✅ Done | 0009 |
| M9 | Book Clubs, Buddy Reads & Events | ✅ Done | 0010 |
| M10 | Reading Tracker | ✅ Done | 0011 |
| M11 | Payments, Orders & Shipping | ✅ Done | 0012 |
| M12 | Professional Sellers & Monetization | ✅ Done | 0014 |
| M13 | Institutions & Donations | ✅ Done | 0013 |
| M14 | Recommendations & AI | ✅ Done | 0015 |

### Totals

| Category | Count |
|---|---|
| Database Tables | 103+ |
| Alembic Migrations | 15 |
| Backend API Endpoints | ~156 |
| Frontend Pages (Web) | 34 |
| Frontend Pages (Admin) | 12 |
| Shared UI Components | 10 |
| Background Job Types | 8 |
| Domain Event Types | 32 |
| State Machines | 10 |
| Notification Types | 20 |

### Service URLs (Local Development)

| Service | URL | Purpose |
|---|---|---|
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Interactive OpenAPI |
| API Health | http://localhost:8000/health/ready | Health check |
| Web App | http://localhost:3000 | Public Next.js frontend |
| Admin App | http://localhost:3001 | Admin Next.js frontend |
| MinIO Console | http://localhost:9001 | Object storage UI |
| PostgreSQL | localhost:5432 | Database (user: oldpages) |
| Redis | localhost:6379 | Cache & pub/sub |

### Key Architectural Decisions

| Decision | Choice | Reason |
|---|---|---|
| Architecture | Modular Monolith | Ship fast, extract later |
| Database | PostgreSQL + PostGIS | Location queries, JSON, reliability |
| Search | PostgreSQL FTS + Trigram | No external service dependency |
| Payments | Provider abstraction | Swap Razorpay/Stripe without code change |
| Shipping | Provider abstraction | Swap Shiprocket/Delhivery easily |
| Auth tokens | JWT (short) + Refresh (rotating) | Security + UX balance |
| Location privacy | PostGIS geohash for public | Never expose exact home address |
| Events | Transactional outbox | Reliable event delivery |
| Idempotency | DB unique keys | Safe payment/order retries |
| Reviews | Transaction-linked | Prevent fake reviews |
| Media | Direct-to-storage upload | No API bottleneck for large files |
| Real-time | WebSocket + Redis pub/sub | Stateless API, scalable |
