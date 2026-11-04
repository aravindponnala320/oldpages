# Payments, Orders, and Shipping API

Milestone 11 adds seller-specific carts, orders, local payment initiation, shipment records,
shipping status updates, disputes, and webhook idempotency in the existing FastAPI modular
monolith.

## Carts and Orders

- `POST /api/v1/carts`
- `GET /api/v1/carts/{cart_id}`
- `POST /api/v1/carts/{cart_id}/items`
- `DELETE /api/v1/carts/{cart_id}/items/{item_id}`
- `POST /api/v1/carts/{cart_id}/checkout`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/accept`
- `POST /api/v1/orders/{order_id}/cancel`

Carts are scoped to one buyer and one seller. Buyers cannot create a cart with themselves as the
seller. Checkout creates an order with subtotal, platform fee, total, fulfillment method, and order
line-item snapshots. Sellers can accept only paid orders, and participants can cancel orders while
they are in cancellable states.

## Payments

- `POST /api/v1/payments/{order_id}/initiate`
- `POST /api/v1/payments/{order_id}/refunds`
- `POST /api/v1/payments/{order_id}/payouts`
- `POST /api/v1/payments/webhook/{provider}`

Payment initiation is available through the local provider and is idempotent per order and
idempotency key. Duplicate webhook provider event IDs are recorded once and return
`already_processed` on replay. Payment capture webhooks transition payments to captured and orders
to paid. Refunds use the payment-provider abstraction and are capped by remaining captured amount.
Seller payouts are available only after delivery/completion and cannot exceed captured funds minus
platform fees, committed refunds, and prior payouts.

## Shipments

- `POST /api/v1/shipments`
- `GET /api/v1/shipments/{shipment_id}`
- `PATCH /api/v1/shipments/{shipment_id}`
- `POST /api/v1/shipments/webhook/{provider}`

Shipments are tied to orders and expose provider, address snapshots, tracking fields, and status.
Only order participants can read shipments. Sellers can create and update shipment status. Shipping
webhooks update shipment tracking/status and move orders to shipped or delivered when provider
events report those milestones.

## Disputes

- `POST /api/v1/disputes`
- `GET /api/v1/disputes/{dispute_id}`
- `POST /api/v1/disputes/{dispute_id}/evidence`
- `POST /api/v1/disputes/{dispute_id}/resolve`

Only order participants can open or view disputes. Evidence is stored on the dispute record, and
resolution records the resolver and resolution timestamp.
