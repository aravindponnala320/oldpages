# Search, Location, and Discovery

Milestone 4 keeps search inside the modular monolith and PostgreSQL database.

## Storage

Search uses canonical catalog tables, listing tables, and the new discovery tables:

- `search_query_logs`
- `saved_searches`
- `wishlist_items`
- `listing_favorites`
- `follows`
- `search_match_notifications`

`listing_locations` now stores rounded `public_latitude` and `public_longitude` values derived
from seller-provided exact coordinates. Exact coordinate strings remain private and are not
returned by public APIs.

## Query Strategy

The runtime query filters active listings and joins book metadata, identifiers, authors,
categories, academic metadata, condition, delivery, and public location. Ranking combines text
match score, listing quality, favorites, freshness, and distance where available.

PostgreSQL migrations add:

- Full-text GIN index for listing title and description
- Trigram indexes for titles, authors, categories, and public location area
- JSONB GIN index for listing modes
- GIST index over public PostGIS geography points for radius search

SQLite tests use the same API behavior with an in-process distance fallback.

## Performance Target

The product target remains search P95 under 700 ms. Milestone 4 includes a local smoke load test
that runs repeated search requests through the ASGI test client and asserts the documented target.
Production-grade load testing with realistic data volume is still required before public launch.

## Privacy

Public search responses expose only:

- `city`
- `state`
- `country`
- `neighborhood`
- `public_area`
- `campus_pickup`

Exact coordinates and private pickup notes are visible only to future accepted transaction flows,
not to search, suggestions, or listing public detail.

## Notifications

Match notifications are persisted as pending rows when a saved search currently has matches. The
notification delivery worker and user notification inbox are intentionally deferred to the
notifications milestone.
