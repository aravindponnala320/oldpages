# OldPages.in — Master Product Requirements and System Architecture

**Version:** 1.0  
**Audience:** Product owner, UX designer, backend engineer, frontend engineer, mobile engineer, DevOps engineer, QA engineer, security reviewer, and Codex/AI coding agents.  
**Primary goal:** Build a trusted marketplace and reader community where people can buy, sell, exchange, lend, rent, request, and donate books locally or across regions.

---

## 1. Product Vision

OldPages.in is a book-first marketplace and social platform.

It combines:

1. Used-book marketplace
2. Book exchange and lending network
3. Reader communities
4. College, school, neighborhood, and city groups
5. Book clubs, buddy reads, and readalongs
6. Personal reading tracker
7. Events and meetups
8. Donation campaigns
9. Professional seller storefronts
10. Trust, safety, payments, shipping, and buyer protection

The product must support the complete lifecycle of a book:

- Discover
- Buy or receive
- Read
- Discuss
- Review
- Resell
- Exchange
- Lend
- Donate

---

## 2. Product Principles

1. Book listings must take less than two minutes to create.
2. Users must never need to expose their exact home address publicly.
3. Trust and safety are core product features, not afterthoughts.
4. Search must work by title, author, ISBN, category, course, institution, and location.
5. Community and marketplace features must be connected.
6. Mobile-first design is mandatory.
7. Accessibility must be designed from the beginning.
8. Build a modular monolith first; extract services only when scale requires it.
9. Use structured offers and transactions instead of relying only on free-form chat.
10. The free product must remain useful; monetization must add convenience, visibility, and professional tools.

---

## 3. Supported Platforms

### Phase 1
- Responsive web application
- Progressive Web App
- Admin web application

### Phase 2
- iOS application
- Android application

### Recommended stack
- Web: Next.js, TypeScript, Tailwind CSS, TanStack Query
- Mobile: React Native with Expo and TypeScript
- Backend: FastAPI, Pydantic, SQLAlchemy 2, Alembic
- Database: PostgreSQL with PostGIS
- Cache and real-time: Redis
- Search: PostgreSQL full-text search initially; OpenSearch later
- Storage: S3-compatible object storage and CDN
- Background jobs: Celery, Dramatiq, or Arq
- Payments: provider abstraction
- Notifications: email, SMS, push, and in-app
- Deployment: Docker and ECS/Fargate or another managed container platform
- Observability: OpenTelemetry, Sentry, structured logs, metrics, dashboards

---

## 4. User Types

### 4.1 Guest
Can:
- Browse public listings
- Search books
- View public communities
- View public profiles
- View public events
- Share listings

Cannot:
- Chat
- Make offers
- Create listings
- Join private communities
- See exact pickup details

### 4.2 Registered User
Can:
- Create listings
- Buy, sell, exchange, lend, rent, donate, and request books
- Chat
- Make structured offers
- Join communities
- Track reading
- Create shelves
- Follow users, authors, sellers, communities, and institutions
- Review completed transactions

### 4.3 Verified User
May have:
- Email verified
- Mobile verified
- Identity verified
- Institution verified
- Address verified
- Business verified

### 4.4 Professional Seller
Can:
- Manage storefront
- Upload inventory in bulk
- Manage staff
- Manage multiple locations
- Use seller analytics
- Run promotions
- Use API and webhooks

### 4.5 Institution
Examples:
- School
- College
- University
- Library
- NGO
- Coaching center
- Publisher
- Bookstore

### 4.6 Community Roles
- Owner
- Administrator
- Moderator
- Event organizer
- Book-club leader
- Verified expert
- Member
- Muted member
- Banned member

### 4.7 Platform Roles
- Support agent
- Moderator
- Trust and safety analyst
- Finance operator
- Content administrator
- Super administrator

---

## 5. Authentication and Account Management

Support:

- Email and password
- Email OTP
- Email magic link
- Mobile number and OTP
- Google sign-in
- Apple sign-in
- Facebook sign-in
- X/Twitter sign-in
- Institutional email verification

Required account features:

- Email verification
- Mobile verification
- Password reset
- Refresh-token rotation
- Session and device management
- Logout from all devices
- Login activity
- Suspicious-login alerts
- Optional two-factor authentication
- Account export
- Account deletion
- Consent management
- Terms and privacy acceptance history

Security requirements:

- Passwords hashed with Argon2id or equivalent
- Short-lived access tokens
- Rotating refresh tokens
- Secure HTTP-only cookies for web
- Secure storage for mobile tokens
- CSRF protection for cookie-authenticated flows
- OAuth state and PKCE
- Brute-force protection
- Rate limiting
- Audit logs for sensitive actions

---

## 6. User Profile

Profile fields:

- Display name
- Username
- Profile image
- Bio
- Approximate location
- Languages
- Favorite genres
- Favorite authors
- Favorite books
- Institution
- Course or department
- Reading interests
- Public shelves
- Community memberships
- Books listed
- Books sold
- Books exchanged
- Books donated
- Rating
- Response rate
- Response time
- Completed transactions
- Followers
- Following
- Badges
- Verification badges

Privacy controls:

- Public, members-only, or private profile
- Hide exact location
- Hide institution
- Hide shelves
- Hide followers and following
- Control who can message
- Control online status
- Control read receipts
- Block and report users

---

## 7. Book Catalog

Separate canonical books from marketplace listings.

### Book
Represents the intellectual work and edition metadata.

Fields:
- Title
- Subtitle
- Description
- Authors
- ISBN-10
- ISBN-13
- Publisher
- Edition
- Publication year
- Language
- Page count
- Format
- Cover image
- Categories
- Genres
- Subjects
- Academic metadata
- External identifiers

### Academic metadata
- School board
- Grade
- Subject
- College
- University
- Degree
- Department
- Course
- Semester
- Professor
- Exam
- Exam year
- Syllabus version

### Listing
Represents one seller's physical copy or inventory item.

---

## 8. Marketplace Listing Types

Every listing supports one or more modes:

- Sell
- Exchange
- Sell or exchange
- Donate
- Lend
- Rent
- Request
- Giveaway
- Bulk sale
- Auction for rare books in a later phase

Listing status:

- Draft
- Pending moderation
- Active
- Reserved
- Sold
- Exchanged
- Donated
- Lent
- Rented
- Expired
- Suspended
- Rejected
- Deleted

---

## 9. Listing Creation

### Fast listing
Required minimum:
- Book title or ISBN
- Listing type
- Price when applicable
- Condition
- At least one actual photo
- Approximate location

### Listing methods
- Scan ISBN barcode
- Search book catalog
- Enter ISBN manually
- Take cover photo
- Upload multiple books
- Copy existing listing
- Relist prior inventory
- Bulk CSV import
- Voice-assisted listing

### Automatically populated
- Title
- Author
- ISBN
- Publisher
- Edition
- Publication year
- Cover
- Category
- Description

### Seller-provided data
- Actual-condition photos
- Condition
- Damage details
- Writing or highlighting
- Missing pages
- Binding condition
- Original accessories
- Price
- Negotiable flag
- Quantity
- Pickup availability
- Shipping availability
- Return policy
- Exchange preferences
- Lending duration
- Rental deposit

### Listing quality score
Calculate from:
- Photo count
- Image quality
- Condition completeness
- ISBN confidence
- Description completeness
- Price completeness
- Location completeness

---

## 10. Condition Model

Top-level condition:

- New and sealed
- Like new
- Excellent
- Very good
- Good
- Acceptable
- Poor
- Reference only

Detailed attributes:

- Highlighting percentage
- Handwritten notes
- Name written inside
- Torn pages
- Missing pages
- Loose binding
- Water damage
- Stains
- Odor or smoke exposure
- Library markings
- Stickers
- Dust jacket present
- Supplemental media present
- Access code status
- Answer key present
- Workbook completion
- Signed by author
- First edition
- Collectible notes

---

## 11. Search and Discovery

Search by:

- Title
- Author
- ISBN
- Publisher
- Edition
- Subject
- Genre
- Description
- School
- Board
- College
- University
- Course
- Semester
- Exam
- Seller
- Community
- Location

Filters:

- Listing type
- Price
- Free
- Distance
- City
- State
- Country
- Condition
- Language
- Category
- Genre
- Author
- Publisher
- Edition
- Publication year
- Format
- Verified seller
- Seller rating
- Individual or professional seller
- Pickup
- Shipping
- Same-day pickup
- Negotiable
- Return accepted
- Recently added
- Recently discounted
- Actual photos
- Signed copy
- First edition
- Rare or collectible
- Large print
- Braille
- Accessible formats

Sorting:

- Relevance
- Nearest
- Newest
- Lowest price
- Highest price
- Best condition
- Highest-rated seller
- Most saved
- Most viewed
- Recently reduced
- Best value
- Fastest delivery
- Recommended

Search features:

- Autocomplete
- Typo tolerance
- Synonyms
- Recent searches
- Trending searches
- Zero-result recovery
- Saved searches
- Match alerts
- Similar books
- Same edition from other sellers
- Nearby alternatives

---

## 12. Location

Use PostGIS.

Features:

- Search within radius
- Approximate public seller location
- Hidden exact home address
- City and neighborhood browsing
- Map view
- List view
- Campus pickup
- Safe public pickup-point suggestions
- Local-only
- Nationwide shipping
- Multiple seller locations
- Location-based community discovery

Location privacy:

- Never expose exact coordinates publicly
- Use rounded/geohash area for public discovery
- Reveal exact pickup point only after accepted transaction
- Allow users to choose public pickup locations

---

## 13. Favorites, Wishlists, Following, and Collections

Features:

- Favorite listing
- Wishlist book
- Saved search
- Follow user
- Follow seller
- Follow author
- Follow genre
- Follow community
- Follow college
- Price alerts
- Availability alerts
- Nearby alerts
- Edition alerts

Shelves:

- Want to read
- Currently reading
- Finished
- Did not finish
- Owned
- Previously owned
- Available for exchange
- Available for lending
- Favorites
- Academic books
- Rare collection
- Custom shelves

---

## 14. Chat

### Chat request flow
1. Buyer opens listing
2. Buyer sends request
3. Seller accepts, declines, or blocks
4. Full conversation opens after acceptance

### Personal chat features
- Text
- Images
- Voice notes
- Listing card
- Offer card
- Exchange card
- Pickup proposal
- Shipping details
- Payment request
- Typing indicator
- Online status
- Read receipts
- Reply
- Reactions
- Message search
- Mute
- Archive
- Block
- Report

### Community chat
- General
- Announcements
- Marketplace
- Events
- Chapters
- Topics
- Moderator-only
- Temporary event channels

### Safety
- Link scanning
- Scam phrase detection
- Contact information warnings
- Rate limiting
- Spam limits
- Attachment scanning
- Message reporting
- Evidence retention for disputes

---

## 15. Offers and Negotiation

Sale offer:
- Amount
- Quantity
- Fulfillment method
- Expiration
- Message

Exchange proposal:
- Offered books
- Requested books
- Cash difference
- Shipping responsibility
- Expiration

Bundle offer:
- Multiple books
- Combined price
- Combined shipping

Statuses:
- Draft
- Pending
- Countered
- Accepted
- Rejected
- Withdrawn
- Expired
- Payment pending
- Reserved
- Completed
- Cancelled
- Disputed

Seller tools:
- Minimum acceptable offer
- Auto-reject low offers
- Disable negotiation
- Reserve listing
- Select buyer
- Counteroffer

---

## 16. Orders and Transactions

Fulfillment types:
- Local pickup
- Seller-arranged shipping
- Integrated shipping
- Digital fulfillment only where legal and licensed

Order lifecycle:
- Created
- Awaiting payment
- Paid
- Accepted
- Preparing
- Ready for pickup
- Shipped
- Delivered
- Completed
- Cancelled
- Refunded
- Disputed

Pickup:
- Time proposals
- Safe pickup points
- Exact details after acceptance
- QR or one-time handover code
- Buyer confirmation
- Seller confirmation
- No-show handling

Shipping:
- Rate calculation
- Label generation
- Tracking
- Carrier webhooks
- Delivery confirmation
- Lost package claim
- Return label
- Package evidence photos

---

## 17. Cart and Checkout

Support:
- Multiple items from one seller
- Seller-specific checkout
- Bundle discount
- Coupon
- Shipping calculation
- Taxes
- Pickup
- Delivery address
- Buyer protection
- Order summary

Do not initially combine multiple peer-to-peer sellers into one payment.

---

## 18. Payments and Payouts

Payment methods:
- UPI
- Credit card
- Debit card
- Net banking
- Wallets
- Cash on pickup
- Cash on delivery where approved
- Store credit
- Promotional credit

Payment capabilities:
- Authorization
- Capture
- Platform fee
- Seller payout
- Partial payout
- Refund
- Partial refund
- Failed payment retry
- Receipts
- Tax invoices
- Payout tracking
- Seller bank verification

Buyer protection:
- Funds held until fulfillment milestone
- Delivery evidence
- Buyer confirmation
- Automatic release after protection window
- Dispute creation
- Evidence upload
- Refund decision
- Appeal

Build a payment-provider abstraction. Do not hard-code business logic to one provider.

---

## 19. Reviews and Reputation

Only completed transactions can produce transaction reviews.

Seller rating dimensions:
- Description accuracy
- Condition accuracy
- Communication
- Packaging
- Shipping speed
- Pickup punctuality

Buyer rating dimensions:
- Communication
- Payment reliability
- Pickup punctuality
- Respectful behavior

Display:
- Average rating
- Rating count
- Completed transactions
- Cancellation rate
- Response rate
- Average response time
- Account age
- Verification badges
- Repeat buyers

---

## 20. Trust and Safety

Internal trust score inputs:
- Verification levels
- Account age
- Transaction history
- Cancellation history
- Disputes
- Reports
- Device risk
- Duplicate accounts
- Payment risk
- Community moderation history

Public labels:
- New member
- Verified member
- Reliable seller
- Highly responsive
- Community contributor
- Top seller

Fraud controls:
- Duplicate listings
- Stolen-image detection
- Suspicious pricing
- Repeated account detection
- IP and device risk
- Unsafe links
- Contact scraping prevention
- Phone-number exposure detection
- Behavioral rate limits
- New-account limits
- High-risk transaction review

Reports:
- Fake listing
- Misleading condition
- Piracy
- Counterfeit
- Scam
- Harassment
- Hate speech
- Sexual content
- Child-safety concern
- Spam
- Fake review
- Payment fraud
- Stolen image
- Copyright infringement
- Personal-information exposure
- Dangerous meetup request

Moderation workflow:
- Automated flag
- User report
- Severity classification
- Moderator queue
- Evidence review
- Temporary restriction
- Warning
- Removal
- Suspension
- Ban
- Appeal
- Audit history

---

## 21. Communities

Communities can be based on:

- College
- University
- School
- Area
- City
- Apartment
- Workplace
- Language
- Genre
- Author
- Series
- Specific book
- Exam
- Course
- Profession
- Age group
- Reading goal
- Library
- Bookstore
- Publisher
- Social cause

Community visibility:
- Public
- Private
- Secret
- Institution verified
- Paid
- Local
- Online only

Community features:
- Description
- Cover image
- Rules
- Membership questions
- Member approval
- Roles
- Channels
- Feed
- Posts
- Comments
- Reactions
- Polls
- Events
- Marketplace tab
- Book clubs
- Resources
- Moderator tools
- Analytics

Community post types:
- Text
- Review
- Photo
- Video
- Poll
- Question
- Recommendation
- Quote
- Reading update
- Listing
- Exchange request
- Donation request
- Event
- Challenge
- Resource

Community moderation:
- Post approval
- Keyword filters
- Link restrictions
- Slow mode
- Member mute
- Member ban
- Warning
- Moderator notes
- Report queue
- Audit history

---

## 22. Book Clubs, Buddy Reads, and Readalongs

Book-club features:
- Current book
- Next book
- Past books
- Nominations
- Voting
- Ranked-choice voting
- Start and end dates
- Milestones
- Chapter schedule
- Meetings
- Attendance
- Calendar sync
- Discussion guides
- Meeting notes
- Shared files
- Club history

Buddy read:
- Small private group
- Shared progress
- Page-based discussion
- Reactions
- Shared deadline
- Progress comparison

Readalong:
- Large group
- Chapter rooms
- Scheduled discussions
- Host announcements
- Milestones
- Moderators
- Public or private participation

Spoiler protection:
- Chapter tag
- Page tag
- Percentage tag
- Whole-book spoiler tag
- Blurred content
- Progress-gated reveal
- Moderator controls

Marketplace integration:
- Show listings for current club book
- Allow group bundle purchase
- Notify members of available copies
- Support community exchange events

---

## 23. Events

Event types:
- Book-club meeting
- Book exchange
- Used-book fair
- Donation drive
- Author meetup
- Signing
- Reading session
- Silent reading
- Children’s story session
- Library event
- College textbook sale
- Writing workshop
- Poetry reading
- Online discussion
- Author interview

Features:
- Date and time
- Time zone
- Map
- Online link
- Capacity
- Waitlist
- RSVP
- Guests
- Ticketing
- Free or paid
- Calendar sync
- Event chat
- Reminders
- Announcements
- QR check-in
- Attendance
- Feedback
- Gallery

---

## 24. Reading Tracker

Track:
- Reading status
- Start date
- Finish date
- Current page
- Percentage
- Daily reading time
- Notes
- Highlights
- Quotes
- Rating
- Review
- Re-read count

Goals:
- Books per year
- Pages per month
- Minutes per day
- Genre challenge
- Author challenge
- Language challenge
- Community challenge
- Institution challenge

Statistics:
- Books completed
- Pages read
- Reading streak
- Genres
- Authors
- Monthly progress
- Yearly report
- Money spent
- Money saved
- Books exchanged
- Books donated

---

## 25. Recommendations

Recommend:
- Books
- Listings
- Sellers
- Communities
- Events
- Book clubs
- Reading challenges

Signals:
- Reading history
- Search history
- Wishlist
- Genres
- Authors
- Communities
- Course or institution
- Similar users
- Price preference
- Location
- Marketplace activity

Every recommendation should include a short explanation.

---

## 26. Donation System

Supported recipients:
- Individuals
- Schools
- Colleges
- Libraries
- NGOs
- Community centers

Donation campaign:
- Organization
- Target books
- Accepted conditions
- Quantity target
- Location
- Pickup or drop-off
- Deadline
- Verification
- Progress
- Impact report

Donation workflow:
1. Campaign created
2. Donor pledges books
3. Eligibility checked
4. Pickup/drop-off arranged
5. Recipient confirms receipt
6. Donor gets confirmation and impact summary

---

## 27. Professional Seller Features

- Business profile
- Storefront
- Logo
- Cover
- Multiple branches
- Inventory
- SKU
- Barcode scanning
- Bulk CSV import
- Bulk editing
- Stock alerts
- Staff accounts
- Orders
- Invoices
- Returns
- Shipping rules
- Analytics
- Coupons
- Bundles
- Followers
- Featured collections
- API
- Webhooks

Analytics:
- Views
- Saves
- Conversion
- Sales
- Revenue
- Average order value
- Best categories
- Slow stock
- Inventory age
- Search impressions
- Returning customers
- Customer geography

---

## 28. Authors, Publishers, Libraries, and NGOs

Author:
- Verified badge
- Biography
- Books
- Events
- AMA sessions
- Signed copies
- Followers
- Announcements

Publisher:
- Verified profile
- Catalog
- New editions
- Clearance inventory
- Review copies
- Events
- Rights-holder reporting

Library:
- Profile
- Donation needs
- Events
- Reading groups
- Surplus distribution
- Membership information

NGO:
- Campaigns
- Needed books
- Pickup points
- Impact reports
- Receipts where applicable

---

## 29. Children and Family Safety

- Parent-managed child profile
- Restricted messaging
- No exact location
- Parent transaction approval
- Age-appropriate communities
- Child-safe event filters
- No unrestricted adult-to-minor direct messaging
- School-managed communities
- Reading challenges
- Safety reporting

---

## 30. Accessibility

Required:
- Screen-reader support
- Keyboard navigation
- High contrast
- Adjustable text size
- Reduced motion
- Alt text
- Captions
- Voice search
- Voice listing
- Accessible forms
- Color-blind-safe indicators
- Large tap targets
- Multi-language interface
- Dyslexia-friendly reading option
- Large-print filter
- Braille filter

Target WCAG 2.2 AA.

---

## 31. Notifications

Types:
- Chat request
- Message
- Offer
- Counteroffer
- Offer accepted
- Payment
- Shipping
- Pickup
- Price drop
- Wishlist match
- Saved search match
- Nearby listing
- Community post
- Comment
- Mention
- Event
- Reading milestone
- Goal reminder
- Security alert
- Support update

Channels:
- In-app
- Push
- Email
- SMS for critical events

Preferences:
- Immediate
- Daily digest
- Weekly digest
- Muted
- Quiet hours

---

## 32. Premium Plans

### Free
- Core marketplace
- Limited active listings
- Basic communities
- Basic reading tracking
- Standard alerts

### OldPages Plus
- More listings
- Advanced filters
- More saved searches
- Instant alerts
- Ad-free
- Advanced reading statistics
- Premium profile options
- More community creation
- Early access to selected listings

### Seller Pro
- Higher listing limits
- Bulk tools
- Storefront
- Analytics
- Repricing
- Inventory import
- Promotions
- Team accounts
- Priority support

### Community Pro
- Large membership
- Multiple moderators
- Advanced events
- Attendance analytics
- Paid events
- Branding
- Scheduled posts
- Advanced moderation
- Resource management

### Institution
- Verified private communities
- Multiple administrators
- Campus marketplace
- Student onboarding
- Policy controls
- Reports
- SSO later
- Data export

Paid promotions:
- Featured listing
- Search boost
- Homepage placement
- Category spotlight
- City spotlight
- Urgent badge
- Weekend boost

---

## 33. Gamification

Badges:
- First listing
- First sale
- First exchange
- First donation
- Trusted seller
- Fast responder
- Helpful reviewer
- Community builder
- Event organizer
- Reading streak
- Genre explorer
- Book rescue champion
- Campus contributor

Points may be earned for:
- Completed transactions
- Donations
- Helpful reviews
- Legitimate reports
- Community participation
- Reading goals
- Hosting events

Never reward positive reviews or spammy engagement.

---

## 34. Admin and Operations

Admin modules:
- Users
- Listings
- Communities
- Reports
- Moderation
- Disputes
- Payments
- Refunds
- Payouts
- Shipping issues
- Categories
- Book metadata
- Promotions
- Subscriptions
- Notification campaigns
- CMS content
- Feature flags
- Audit logs
- Fraud dashboard
- Analytics
- Support tickets

Support:
- Help center
- Guided issue flow
- Ticketing
- Transaction-linked cases
- Evidence upload
- SLA priority
- Resolution history
- Satisfaction survey

---

## 35. Non-Functional Requirements

### Performance
- P95 API latency under 300 ms for normal reads
- Search P95 under 700 ms
- Chat message acknowledgement under 500 ms
- Initial mobile web content under 2.5 seconds on common networks
- Image upload with resumable strategy for large files

### Availability
- Target 99.9% after production maturity
- Graceful degradation when search, notifications, or recommendations are unavailable

### Scalability
- Horizontally scalable stateless API
- Redis for ephemeral state
- Background workers for heavy operations
- CDN for media
- Read replicas when required

### Reliability
- Idempotency for payments, orders, offers, notifications, imports, and webhooks
- Retry with exponential backoff
- Dead-letter queues
- Outbox pattern for reliable events
- Database constraints for business invariants

### Security
- OWASP ASVS-informed controls
- Least privilege
- Secrets manager
- Encryption in transit and at rest
- PII data classification
- Data retention policy
- Audit trail
- Dependency scanning
- Container scanning
- SAST and DAST
- Abuse-rate limits

### Privacy
- Consent records
- Account deletion
- Data export
- Data minimization
- Location privacy
- Child-safety rules
- Configurable retention

### Localization
- Internationalization-ready strings
- Currency abstraction
- Time-zone aware dates
- Country-specific address formats
- Multi-language content

---

## 36. Recommended Architecture

Use a modular monolith.

```text
clients/
  web/
  mobile/
  admin/

backend/
  app/
    identity/
    users/
    institutions/
    catalog/
    listings/
    search/
    locations/
    favorites/
    communities/
    posts/
    clubs/
    reading/
    events/
    chat/
    offers/
    orders/
    payments/
    shipping/
    reviews/
    trust_safety/
    donations/
    notifications/
    subscriptions/
    analytics/
    admin/
  shared/
    db/
    cache/
    events/
    security/
    storage/
    observability/
    configuration/
```

Each backend module should contain:

```text
router.py
schemas.py
models.py
service.py
repository.py
permissions.py
exceptions.py
tasks.py
events.py
tests/
```

Rules:
- Routers validate transport-level input
- Services contain business rules
- Repositories contain persistence logic
- Models define database state
- Schemas define API contracts
- Permissions centralize authorization
- Tasks contain background work
- Events publish domain changes

---

## 37. Infrastructure Architecture

```text
Users
  |
CDN / WAF
  |
Load Balancer
  |
FastAPI API instances
  |------ PostgreSQL + PostGIS
  |------ Redis
  |------ Object Storage
  |------ Search
  |------ Background Queue
  |------ WebSocket gateway
  |
Workers
  |------ media processing
  |------ email/SMS/push
  |------ search indexing
  |------ fraud checks
  |------ payment webhooks
```

Recommended production components:
- CloudFront or equivalent CDN
- WAF
- Managed PostgreSQL
- Managed Redis
- S3-compatible storage
- ECS/Fargate
- Queue service
- Secrets manager
- Central logs
- Metrics and alerts

Avoid Kubernetes initially unless the team already has strong operational experience.

---

## 38. Database Entities

### Identity
- users
- user_profiles
- user_sessions
- user_devices
- social_accounts
- user_verifications
- user_preferences
- user_blocks
- consents

### Institutions
- institutions
- institution_domains
- institution_members
- institution_roles

### Catalog
- books
- book_editions
- authors
- book_authors
- publishers
- categories
- book_categories
- book_identifiers
- academic_metadata

### Marketplace
- listings
- listing_images
- listing_conditions
- listing_locations
- listing_delivery_methods
- listing_price_history
- listing_views
- listing_saves
- listing_inventory

### Discovery
- saved_searches
- wishlists
- follows
- recommendations

### Communities
- communities
- community_members
- community_roles
- community_rules
- community_channels
- community_posts
- post_comments
- post_reactions
- community_reports

### Reading
- shelves
- shelf_items
- reading_progress
- reading_notes
- reading_goals
- reading_statistics

### Clubs and Events
- book_clubs
- club_books
- book_nominations
- book_votes
- reading_milestones
- buddy_reads
- readalongs
- events
- event_rsvps
- event_waitlists
- event_checkins

### Communication
- chat_requests
- conversations
- conversation_members
- messages
- message_attachments
- message_reads

### Commerce
- offers
- exchange_offer_items
- carts
- cart_items
- orders
- order_items
- payments
- payouts
- refunds
- shipments
- pickup_sessions
- disputes

### Trust and Safety
- reviews
- reports
- moderation_cases
- moderation_actions
- risk_events
- device_risk
- audit_logs

### Monetization
- subscription_plans
- subscriptions
- promotions
- promotion_orders
- coupons
- business_profiles
- staff_accounts
- inventory_imports

### Donation
- donation_campaigns
- donation_needs
- donation_pledges
- donation_receipts

### Notifications
- notifications
- notification_preferences
- notification_deliveries

---

## 39. API Groups

```text
/api/v1/auth/*
/api/v1/users/*
/api/v1/verifications/*
/api/v1/institutions/*
/api/v1/books/*
/api/v1/listings/*
/api/v1/search/*
/api/v1/locations/*
/api/v1/favorites/*
/api/v1/wishlists/*
/api/v1/follows/*
/api/v1/communities/*
/api/v1/posts/*
/api/v1/clubs/*
/api/v1/reading/*
/api/v1/events/*
/api/v1/chat-requests/*
/api/v1/conversations/*
/api/v1/offers/*
/api/v1/carts/*
/api/v1/orders/*
/api/v1/payments/*
/api/v1/shipments/*
/api/v1/reviews/*
/api/v1/reports/*
/api/v1/disputes/*
/api/v1/donations/*
/api/v1/notifications/*
/api/v1/subscriptions/*
/api/v1/promotions/*
/api/v1/business/*
/api/v1/admin/*
```

All list endpoints require:
- Pagination
- Stable sorting
- Filtering
- Field validation
- Permission checks
- Rate limits where applicable

Use cursor pagination for large feeds, chat, notifications, and search results.

---

## 40. Domain Events

```text
USER_REGISTERED
USER_VERIFIED
LISTING_CREATED
LISTING_PUBLISHED
LISTING_UPDATED
LISTING_RESERVED
LISTING_COMPLETED
LISTING_FLAGGED
CHAT_REQUESTED
CHAT_ACCEPTED
MESSAGE_SENT
OFFER_CREATED
OFFER_COUNTERED
OFFER_ACCEPTED
ORDER_CREATED
ORDER_PAID
ORDER_SHIPPED
ORDER_DELIVERED
TRANSACTION_COMPLETED
REVIEW_CREATED
COMMUNITY_CREATED
COMMUNITY_JOINED
POST_CREATED
EVENT_CREATED
EVENT_RSVP_CREATED
BOOK_CLUB_BOOK_SELECTED
READING_PROGRESS_UPDATED
READING_GOAL_COMPLETED
DONATION_PLEDGED
DONATION_RECEIVED
REPORT_CREATED
MODERATION_ACTION_TAKEN
SUBSCRIPTION_STARTED
PROMOTION_PURCHASED
```

Use the transactional outbox pattern to publish reliably.

---

## 41. Permissions

Use RBAC plus resource ownership and contextual checks.

Examples:
- Only listing owner can edit listing
- Only accepted chat participants can read private conversation
- Only completed transaction participants can review
- Only community moderators can remove posts
- Only institution admins can approve institution members
- Exact pickup details visible only after accepted transaction
- Child accounts cannot receive unrestricted adult direct messages
- Support access to private data must be logged

---

## 42. Caching

Cache:
- Public listing detail
- Category tree
- Book metadata
- Search suggestions
- Community summaries
- User public profiles
- Feature flags

Do not cache:
- Sensitive private messages in shared public caches
- Payment state without strong invalidation
- Authorization decisions longer than necessary

Use cache versioning and explicit invalidation events.

---

## 43. Search Indexing

Index document should include:
- Listing ID
- Book metadata
- Seller trust summary
- Price
- Condition
- Location
- Availability
- Fulfillment methods
- Institution
- Community visibility
- Promotion score
- Created date

Ranking signals:
- Text relevance
- Distance
- Freshness
- Condition
- Seller trust
- Price competitiveness
- Listing quality
- Engagement
- Promotion score with clear labeling

Never allow promotion to fully override relevance or safety.

---

## 44. Media Pipeline

1. Client requests upload URL
2. Client uploads directly to storage
3. Backend records pending media
4. Worker scans malware
5. Worker removes metadata
6. Worker creates thumbnails
7. Worker runs moderation
8. Media becomes available
9. CDN serves approved variants

Store original separately from public optimized variants.

---

## 45. Testing Strategy

### Unit tests
- Services
- Validators
- Pricing
- Permissions
- State transitions
- Trust calculations

### Integration tests
- Database repositories
- API endpoints
- Redis
- Search
- Object storage
- Payment provider sandbox
- Webhooks

### Contract tests
- Web/mobile API contracts
- Payment provider contracts
- Shipping provider contracts

### End-to-end tests
- Registration
- Listing creation
- Search
- Chat request
- Offer
- Payment
- Pickup
- Shipping
- Review
- Community join
- Book-club flow
- Report and moderation

### Security tests
- IDOR
- Broken access control
- Rate limit bypass
- CSRF
- XSS
- SQL injection
- File upload attacks
- OAuth account-linking attacks
- Webhook forgery

### Performance tests
- Search
- Feed
- Chat
- listing upload
- Popular event RSVP
- Bulk inventory import

---

## 46. Observability

Logs:
- Structured JSON
- Correlation ID
- User ID where lawful
- Request ID
- Trace ID
- No secrets or unnecessary PII

Metrics:
- API latency
- Error rate
- Database latency
- Cache hit rate
- Queue depth
- Job failures
- WebSocket connections
- Search latency
- Payment failures
- Notification failures
- Moderation backlog

Tracing:
- API to database
- API to cache
- API to provider
- Worker pipelines

Alerts:
- High error rate
- Payment webhook failure
- Queue backlog
- Database saturation
- Search failure
- Elevated fraud reports
- Storage processing backlog

---

## 47. Analytics

Marketplace funnel:
- Registration
- Verification
- Listing started
- Listing completed
- Search
- Listing view
- Save
- Chat request
- Offer
- Accepted offer
- Payment
- Delivery
- Review
- Repeat transaction

Community metrics:
- Daily active members
- Posts
- Comments
- Events
- RSVPs
- Attendance
- Club participation
- Member retention
- Reports

Marketplace health:
- Active listings
- Unique books
- Buyer/seller ratio
- Zero-result rate
- Time to first message
- Time to transaction
- Sell-through rate
- Cancellation
- Dispute
- Repeat buyer
- Repeat seller

---

## 48. UX Navigation

### Mobile bottom navigation
- Home
- Explore
- Sell
- Communities
- Inbox

### Home
- Personalized feed
- Nearby books
- Wishlist matches
- Community updates
- Current reading
- Upcoming events

### Explore
- Marketplace
- Books
- Authors
- Communities
- Events
- People
- Institutions

### Sell
- Scan ISBN
- Add one book
- Add multiple books
- Request book
- Donate
- Import inventory

### Communities
- My communities
- Discover
- Book clubs
- Buddy reads
- Local groups
- Institution groups

### Inbox
- Chat requests
- Messages
- Offers
- Orders
- Community messages
- Support

---

## 49. Delivery Phases

### Phase 0 — Foundation
- Monorepo
- CI/CD
- Configuration
- Database
- Authentication skeleton
- Logging
- Testing
- Design system
- API conventions

### Phase 1 — Marketplace MVP
- Registration
- Profile
- Listings
- ISBN
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

### Phase 2 — Community
- Communities
- Roles
- Feed
- Posts
- Polls
- Events
- Clubs
- Buddy reads
- Readalongs
- Spoiler protection
- Reading tracker

### Phase 3 — Commerce
- Payments
- Shipping
- Buyer protection
- Refunds
- Seller payouts
- Cart
- Professional sellers
- Promotions
- Premium plans

### Phase 4 — Institutions and Donations
- Institution verification
- Campus marketplace
- School and college groups
- Libraries
- NGOs
- Donation campaigns
- Institutional plans

### Phase 5 — Intelligence and Scale
- Recommendation engine
- AI listing assistant
- Condition suggestions
- Price intelligence
- Fraud scoring
- OpenSearch
- Service extraction where justified

---

## 50. Definition of Done

A feature is done only when:

- Product behavior is documented
- UX states are defined
- API contract is defined
- Authorization is implemented
- Validation is implemented
- Errors are handled
- Audit requirements are met
- Unit tests pass
- Integration tests pass
- End-to-end happy path passes
- Accessibility review passes
- Security review passes
- Metrics and logs exist
- Documentation is updated
- Migration and rollback plan exist
- Feature flag exists for risky releases

---

## 51. Product Decisions to Keep

1. Separate canonical books from listings.
2. Use structured offers.
3. Require transaction-linked reviews.
4. Hide exact home location.
5. Launch marketplace before complex social features.
6. Build communities as a core domain, not a generic comments page.
7. Connect communities to marketplace inventory.
8. Use a modular monolith.
9. Use PostGIS from the beginning.
10. Use provider abstractions for auth, payments, shipping, notifications, and search.
11. Preserve audit trails.
12. Implement idempotency for every external side effect.
13. Keep child safety and privacy in the initial design.
14. Design for web and mobile API reuse.
15. Do not build microservices without measured need.

---

## 52. Final Product Statement

OldPages.in is a trusted marketplace and community where people can buy, sell, exchange, lend, rent, request, donate, discover, discuss, and enjoy books locally or across regions.

The system should allow a user to:

1. Discover a book
2. Compare copies
3. Contact a trusted seller
4. Make an offer
5. Pay or arrange pickup
6. Receive the book
7. Track reading
8. Join a discussion
9. Review the experience
10. Resell, exchange, lend, or donate the book

That complete lifecycle is the core product advantage.
