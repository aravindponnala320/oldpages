# ADR 0008: Direct-to-Storage Media Upload

## Status

Accepted.

## Context

Listing images can be large and should not pass through API workers in production. The system also needs a media-processing lifecycle before images become public.

## Decision

Use a direct-to-storage upload pattern:

1. Authenticated client requests an upload URL.
2. API records a `pending_upload` media asset.
3. Client uploads to object storage.
4. Client marks upload complete.
5. Worker processing later scans, strips metadata, creates variants, moderates, and approves public URLs.

Milestone 3 returns development upload URLs and stores lifecycle state. It does not implement real signed URLs or worker processing yet.

## Consequences

API instances stay stateless and avoid large request bodies. Media is not public until approved. Later production work must replace development URLs with provider-signed uploads and implement processing workers.
