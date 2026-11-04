# Business, Subscriptions, Promotions, and Coupons API

Milestone 12 adds professional seller profiles, business locations, staff records, inventory import
records, subscription plans, subscriptions, paid promotions, and coupon validation.

## Business Profiles

- `POST /api/v1/business`
- `GET /api/v1/business`
- `GET /api/v1/business/{profile_id}`
- `PATCH /api/v1/business/{profile_id}`

Each user can create one business profile. Business child resources are protected by scoped staff
permissions. Owners receive all permissions; invited staff receive either role defaults or explicit
permissions from the invite request.

## Locations, Staff, and Imports

- `POST /api/v1/business/{profile_id}/locations`
- `DELETE /api/v1/business/{profile_id}/locations/{location_id}`
- `GET /api/v1/business/{profile_id}/staff`
- `POST /api/v1/business/{profile_id}/staff`
- `DELETE /api/v1/business/{profile_id}/staff/{user_id}`
- `POST /api/v1/business/{profile_id}/imports`
- `GET /api/v1/business/{profile_id}/imports/{import_id}`
- `GET /api/v1/business/{profile_id}/imports/{import_id}/errors.csv`

Locations, staff, and imports are permission-scoped. Inventory import requests are idempotent by
idempotency key or deterministic payload hash. Rows are validated synchronously for the MVP, and
failed rows can be downloaded as CSV from the import error-report endpoint.

Current limitation: bulk edit operations and analytics dashboards are not implemented yet.

## Subscriptions

- `GET /api/v1/subscription-plans`
- `POST /api/v1/subscriptions`
- `GET /api/v1/subscriptions/me`
- `GET /api/v1/subscriptions/entitlements/me`
- `DELETE /api/v1/subscriptions/{subscription_id}`

Subscriptions use local provider records. Users can have only one active subscription, and only the
subscription owner can cancel. Entitlements are centralized in the entitlements endpoint and lapsed
subscriptions are marked expired before premium access is returned.

## Promotions and Coupons

- `POST /api/v1/promotions`
- `GET /api/v1/promotions/me`
- `DELETE /api/v1/promotions/{promotion_id}`
- `POST /api/v1/coupons/validate`
- `POST /api/v1/coupons`
- `GET /api/v1/coupons`

Sellers can promote only their own listings. Coupon validation supports percent and fixed discounts,
minimum order values, activation windows, and max-use checks.
Promotion creation creates a local paid promotion order. Coupon creation and listing require the
`users.is_superuser` platform-admin flag.
