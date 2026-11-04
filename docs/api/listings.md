# Listings and Media API

Milestone 3 adds draft listings, condition/location details, listing images, inventory, price history, and a placeholder direct-to-storage media flow.

## Listing Endpoints

- `POST /api/v1/listings`
- `GET /api/v1/listings/{listing_id}`
- `PATCH /api/v1/listings/{listing_id}`
- `POST /api/v1/listings/{listing_id}/publish`
- `POST /api/v1/listings/{listing_id}/pause`
- `POST /api/v1/listings/{listing_id}/relist`
- `DELETE /api/v1/listings/{listing_id}`

Create accepts either `book_id` or `isbn`. ISBN creation resolves against the local catalog; it does not create new catalog metadata automatically.

Supported listing modes:

- `sell`
- `exchange`
- `sell_exchange`
- `donate`
- `lend`
- `rent`
- `request`
- `giveaway`
- `bulk_sale`

Price is required for `sell`, `sell_exchange`, `rent`, and `bulk_sale`. Donate, giveaway, and request listings cannot carry a sale price.

## State Transitions

- `draft`, `paused`, `expired` -> `active` by publish/relist when validation passes
- `active` -> `paused`
- editable statuses: `draft`, `active`, `paused`, `expired`
- deleted listings are soft-deleted and hidden from public reads

Publish requires:

- condition details
- approximate public location
- available inventory
- at least one uploaded or approved image
- required price when the mode needs one

## Media Endpoints

- `POST /api/v1/media/upload-url`
- `POST /api/v1/media/{media_id}/complete`

Upload URL creation validates content type and size, records a `pending_upload` media asset, and returns a development upload URL. Completing an upload marks the asset `uploaded` and queues placeholder processing.

Media is not public until it is approved by a later processing/moderation worker. Uploaded-but-unapproved media returns `public_url: null`.

## Location Privacy

Create and update can store exact coordinates and private pickup notes. Public listing responses expose only country, state, city, neighborhood, public area, and campus pickup.
