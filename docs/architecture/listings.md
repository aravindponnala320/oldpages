# Listings Architecture

Milestone 3 adds the `listings` module to the modular monolith.

```text
oldpages_api/listings/
  router.py
  schemas.py
  models.py
  repository.py
  service.py
  permissions.py
  exceptions.py
  events.py
  tasks.py
```

## Data Model

- `Listing` owns seller, edition reference, modes, status, price fields, and quality score.
- `ListingCondition` stores detailed physical-condition attributes.
- `ListingLocation` stores exact/private location fields but responses expose only approximate fields.
- `ListingDeliveryMethod` stores pickup/shipping availability.
- `ListingInventory` stores current quantity.
- `ListingPriceHistory` preserves price changes.
- `MediaAsset` tracks upload, scan, and approval lifecycle.
- `ListingImage` connects approved or uploaded media to a listing.

## Service Rules

Routers stay transport-only. `ListingService` owns catalog resolution, owner authorization, state transitions, publish readiness checks, quality scoring, and media lifecycle. `ListingRepository` owns eager-loading so responses do not trigger async lazy-loading.

## Current Media Pipeline

The direct-to-storage flow is represented by database records and development upload URLs. Malware scanning, EXIF removal, thumbnails, and moderation are placeholders in `tasks.py` for a later worker milestone.
