# Commerce

Milestone 6 keeps offers, pickup, transactions, and reviews in the modular monolith.

## Storage

Commerce uses these tables:

- `offers`
- `exchange_offer_items`
- `transactions`
- `pickup_sessions`
- `reviews`
- `review_dimensions`

Listings remain the source of inventory truth. Accepted offers update `listing_inventory` and
create `transactions` in one database transaction.

## Reservation Strategy

Offer acceptance uses a conditional inventory update:

```text
quantity_available = quantity_available - requested_quantity
where quantity_available >= requested_quantity
```

If the update affects no rows, the offer cannot reserve inventory. This prevents two buyers from
reserving the last copy even when both offers were created while inventory was available.

## Pickup Privacy

Public listing APIs continue to expose approximate location only. Exact pickup coordinates,
private notes, and handover codes are stored on `pickup_sessions` and returned only after a
transaction exists and only to transaction participants.

## Reviews

Reviews are keyed to completed transactions. A unique constraint on `transaction_id` and
`reviewer_user_id` enforces one review per side. Rating aggregation and public reputation surfaces
are deferred to later trust/reputation work.
