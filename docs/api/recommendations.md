# Recommendations API

Milestone 14 adds rule-based recommendation surfaces, similar listings, category suggestions, price
suggestions, dismiss/click tracking, and feedback.

## Personal Recommendations

- `GET /api/v1/recommendations`
- `POST /api/v1/recommendations/refresh`
- `POST /api/v1/recommendations/{rec_id}/dismiss`
- `POST /api/v1/recommendations/{rec_id}/click`
- `POST /api/v1/recommendations/{rec_id}/feedback`

Recommendations are generated from local rule-based signals such as wishlist, reading history, and
trending listing data. Each recommendation includes an entity type, entity ID, score, source, and
human-readable reason, plus provider, model, model version, and confidence metadata.

## Suggestions and Similar Listings

- `GET /api/v1/recommendations/category-suggestions`
- `GET /api/v1/recommendations/price-suggestion`
- `GET /api/v1/recommendations/condition-suggestion`
- `GET /api/v1/recommendations/listing-description`
- `GET /api/v1/recommendations/fraud-priority`
- `GET /api/v1/listings/{listing_id}/similar`

Category suggestions use keyword rules. Price suggestions use active listing prices for the same
book and adjust by condition multiplier. Similar listings return active listings for the same book
with available inventory.
Condition suggestions, listing-description assistance, and fraud-priority moderation are rule-based
for the MVP. Assistance responses require human confirmation, are visibly editable by clients, and
include provider/model/version/confidence metadata. Fraud-priority output is review-only and never
authorizes automatic moderation action by itself.

Current limitation: user correction feedback for assistance suggestions is not persisted yet.
