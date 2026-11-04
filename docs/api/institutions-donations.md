# Institutions and Donations API

Milestone 13 adds institution profiles, membership, institution verification, donation campaigns,
pledges, recipient confirmation, and receipts.

## Institutions

- `POST /api/v1/institutions`
- `GET /api/v1/institutions`
- `GET /api/v1/institutions/{institution_id}`
- `PATCH /api/v1/institutions/{institution_id}`
- `POST /api/v1/institutions/{institution_id}/join`
- `GET /api/v1/institutions/{institution_id}/members`
- `POST /api/v1/institutions/{institution_id}/approve-member`
- `DELETE /api/v1/institutions/{institution_id}/members/{user_id}`
- `POST /api/v1/institutions/{institution_id}/domains`
- `POST /api/v1/institutions/{institution_id}/domains/{domain}/verify`
- `POST /api/v1/institutions/{institution_id}/verify`

Institution owners are created as active admins. Non-admin users cannot verify institutions or list,
approve, or remove members. Joining creates a pending membership until an institution admin approves
it. Domain verification is admin-only and does not grant institution admin membership by itself.

## Donation Campaigns

- `POST /api/v1/donations/campaigns`
- `GET /api/v1/donations/campaigns`
- `GET /api/v1/donations/campaigns/{campaign_id}`
- `GET /api/v1/donations/campaigns/{campaign_id}/impact`
- `PATCH /api/v1/donations/campaigns/{campaign_id}`
- `POST /api/v1/donations/campaigns/{campaign_id}/publish`

Campaigns start as drafts and can be published by the campaign owner. Campaigns can list accepted
book conditions and donation needs. Public impact summaries expose aggregate pledge, receipt, and
need progress counts without donor identifiers or donor notes.

## Pledges and Receipts

- `POST /api/v1/donations/campaigns/{campaign_id}/pledge`
- `GET /api/v1/donations/campaigns/{campaign_id}/pledges`
- `GET /api/v1/donations/pledges/me`
- `POST /api/v1/donations/campaigns/{campaign_id}/pledges/{pledge_id}/accept`
- `POST /api/v1/donations/campaigns/{campaign_id}/pledges/{pledge_id}/received`
- `POST /api/v1/donations/campaigns/{campaign_id}/pledges/{pledge_id}/receipt`

Pledges are allowed only for active campaigns. If a campaign defines accepted conditions, pledge
condition is checked case-insensitively before the pledge is created. Only the campaign owner can
accept pledges, mark received, and issue receipts.
