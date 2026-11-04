# Commerce API

Milestone 6 adds structured offers, pickup sessions, transactions, and transaction-linked reviews.

## Offers

- `POST /api/v1/offers`
- `POST /api/v1/offers/{offer_id}/counter`
- `POST /api/v1/offers/{offer_id}/accept`
- `POST /api/v1/offers/{offer_id}/reject`
- `POST /api/v1/offers/{offer_id}/withdraw`

Offers require an active listing with available inventory. Buyers can create price, exchange, and
bundle offers. Counteroffers keep the original buyer, seller, and listing but switch the proposer
to the participant making the counter.

Only the non-proposer can accept or reject an offer. Only the proposer can withdraw it. Expired
offers cannot be accepted.

Accepting an offer creates a reserved transaction and decrements listing inventory in the same
database transaction. If the accepted offer reserves the last copy, the listing moves to
`reserved`.

## Pickup Sessions

- `POST /api/v1/pickups`
- `POST /api/v1/pickups/{pickup_id}/confirm`

Pickup sessions require a reserved pickup transaction. Only transaction participants can create or
confirm pickup sessions. Exact pickup details and handover codes are returned only to accepted
transaction participants.

## Transactions

- `POST /api/v1/transactions/{transaction_id}/complete`

Pickup transactions require a confirmed pickup session and the one-time handover code. Completion
marks the transaction complete and marks the listing complete when no inventory remains.

## Reviews

- `POST /api/v1/reviews`

Reviews require a completed transaction. Each participant can review the transaction once. Buyer
reviews target the seller; seller reviews target the buyer.
