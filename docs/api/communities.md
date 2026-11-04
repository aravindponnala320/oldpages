# Communities API

Milestone 8 adds community creation, discovery, membership approval, feeds, posts, comments,
reactions, reports, and scoped marketplace browsing.

## Communities

- `POST /api/v1/communities`
- `GET /api/v1/communities`
- `GET /api/v1/communities/{community_id}`

Authenticated users can create public, private, secret, or institution-verified communities. The
creator is added as the active owner and default owner, moderator, and member roles are created.
Default `general` and `marketplace` channels are created when the request does not supply channels.

Discovery supports `city`, `country`, `institution`, `genre`, `book_id`, cursor, and limit filters.
Secret communities are not returned by discovery. Private and institution-verified communities can
be discovered, but detail, feed, posts, and marketplace content require active membership.

## Membership

- `POST /api/v1/communities/{community_id}/join`
- `POST /api/v1/communities/{community_id}/approve-member`

Open communities add joiners as active members immediately. Approval and request communities create
pending memberships. Institution-verified communities require the joining user's profile
`institution` to match the community institution and then activate membership immediately.

Member approval is scoped to the target community. Owners and moderators can approve only within
communities where they are active members with moderator permissions.

## Feed

- `POST /api/v1/communities/{community_id}/posts`
- `GET /api/v1/communities/{community_id}/feed`
- `POST /api/v1/posts/{post_id}/comments`
- `POST /api/v1/posts/{post_id}/reactions`

Active members can create posts, comments, and reactions. Post types include text, review, photo,
video, poll, question, recommendation, quote, reading update, listing, exchange request, donation
request, event, challenge, resource, and announcement. Poll posts require at least two options.
Listing posts require `listing_id`.

Only community moderators can create pinned posts or announcements. Feed responses return published
posts ordered with pinned posts first, then newest first, including comment counts, reaction counts,
and the viewer's reaction when present.

## Marketplace and Reports

- `GET /api/v1/communities/{community_id}/marketplace`
- `POST /api/v1/communities/{community_id}/reports`

The community marketplace tab returns active listing responses filtered by the community scope:
book edition, city/state/country, institution, or a combination of those fields. Listing ownership
and transaction flows remain in the listing and commerce domains.

Community reports create `community_reports` rows for community, post, comment, or member targets.
Full moderator queues and community-specific enforcement actions are deferred to later moderation
milestones.
