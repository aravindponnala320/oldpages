# Reading Tracker API

Milestone 10 adds personal reading shelves, progress, notes, goals, and recomputable statistics
inside the existing FastAPI modular monolith.

## Shelves

- `POST /api/v1/reading/shelves`
- `GET /api/v1/reading/shelves`
- `GET /api/v1/users/{user_id}/shelves`
- `POST /api/v1/reading/shelves/{shelf_id}/items`
- `DELETE /api/v1/reading/shelves/{shelf_id}/items/{book_id}`

Authenticated users get default system shelves for want-to-read, currently-reading, finished,
did-not-finish, owned, previously-owned, exchange/lending availability, favorites, academic books,
and rare collections. Custom shelves are supported with per-shelf public/private visibility.

Public shelf listing returns only public shelves unless the viewer is the owner. If the profile
privacy flag hides shelves, public shelf listing returns an empty result for non-owners.

## Progress

- `PUT /api/v1/reading/progress/{book_id}`
- `GET /api/v1/reading/progress`

Progress is stored once per user and book edition. Repeating the same update is idempotent: the row
is updated in place, and daily reading minutes are set for the progress date rather than appended.
Current page can derive percent complete when the catalog edition has a page count. Progress status
also adds the book to the matching system shelf.

## Notes

- `POST /api/v1/reading/notes`
- `GET /api/v1/reading/notes`
- `GET /api/v1/users/{user_id}/reading-notes`

Notes support notes, highlights, and quotes with optional page or percentage anchors. Private notes
are returned only to the owner. The public endpoint returns only notes marked `public`. A
`client_note_id` may be supplied for idempotent note creation.

## Goals and Challenges

- `POST /api/v1/reading/goals`
- `GET /api/v1/reading/goals`

Goals support books per year, pages per month, minutes per day, genre, author, language, community
challenge, and institution challenge goal types. Goal periods store an IANA timezone. Community
challenge goals require active membership in the target community. Institution goals require the
actor profile institution to match the goal institution metadata.

## Statistics

- `POST /api/v1/reading/statistics/recompute`
- `GET /api/v1/reading/statistics`

Statistics are materialized summaries by month, year, or all-time period. Recompute reads the
progress ledger and upserts one statistic per user, period, period start, and timezone. The summary
includes completed books, pages, reading minutes, longest streak, genre counts, author counts,
monthly progress, and year summary JSON.
