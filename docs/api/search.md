# Search and Discovery API

Milestone 4 adds public listing discovery plus authenticated user collections.

## Public Search

`GET /api/v1/search/listings`

Supported query fields include:

- `q`
- `author`
- `isbn`
- `category`
- `city`, `state`, `country`
- `listing_mode`
- `condition`
- `delivery_method`
- `min_price_amount_cents`, `max_price_amount_cents`, `free_only`
- `latitude`, `longitude`, `distance_km`
- `sort`
- `cursor`, `limit`

Sort values are `relevance`, `nearest`, `newest`, `lowest_price`, `highest_price`,
`best_condition`, and `most_saved`. `nearest` and `distance_km` require both
`latitude` and `longitude`.

Responses include approximate public location only. Exact coordinates and private pickup notes
are never returned from search results.

Zero-result searches are written to `search_query_logs` for recovery and analytics.

## Suggestions

`GET /api/v1/search/suggestions?q=god`

Suggestions are returned from active listing data for titles, authors, ISBNs, categories, and
public locations.

## Saved Searches

- `POST /api/v1/saved-searches`
- `GET /api/v1/saved-searches`

Saved searches require authentication. Creating one stores the query, filters, sort, and the
current match count. If matches exist and notifications are enabled, a pending
`search_match_notifications` row is queued for the future notification worker.

## Wishlists, Favorites, and Follows

- `POST /api/v1/wishlists/{book_id}`
- `DELETE /api/v1/wishlists/{book_id}`
- `POST /api/v1/listings/{listing_id}/favorite`
- `DELETE /api/v1/listings/{listing_id}/favorite`
- `POST /api/v1/follows`
- `DELETE /api/v1/follows/{follow_id}`

All mutation endpoints require authentication. Repeated wishlist, favorite, and follow creation
returns the existing resource rather than creating duplicates.
