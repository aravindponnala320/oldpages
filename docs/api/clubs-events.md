# Clubs, Buddy Reads, Readalongs, and Events API

Milestone 9 adds reading-group coordination and public event primitives inside the existing
FastAPI modular monolith.

## Book Clubs

- `POST /api/v1/clubs`
- `GET /api/v1/clubs`
- `GET /api/v1/clubs/{club_id}`

Authenticated users can create public or private book clubs. Clubs may be linked to a community;
community-linked clubs require the creator to be an active member of that community. Public clubs
are discoverable, while private clubs are visible only to the owner in this milestone.

## Club Books, Nominations, and Voting

- `POST /api/v1/clubs/{club_id}/books`
- `GET /api/v1/clubs/{club_id}/books`
- `POST /api/v1/clubs/{club_id}/nominations`
- `POST /api/v1/clubs/{club_id}/votes`
- `POST /api/v1/clubs/{club_id}/select-book`

Club owners can manually add current, next, or past books. Members of visible clubs can nominate
books and cast ranked votes per cycle. Selecting a book uses deterministic ordering: nominations
with votes beat no-vote nominations, lower total rank wins, higher vote count breaks ties, then
nomination creation order and database ID break remaining ties.

Club book responses include active marketplace listings for the selected book edition.

## Reading Milestones and Spoilers

- `POST /api/v1/club-books/{club_book_id}/milestones`
- `GET /api/v1/club-books/{club_book_id}/milestones`

Club owners can create chapter, page, percent, or whole-book milestones. Milestone listing accepts
`progress_type`, `progress_value`, and `finished`; responses hide `discussion_prompt` and set
`spoiler_locked=true` when the reader has not reached the milestone.

## Buddy Reads and Readalongs

- `POST /api/v1/buddy-reads`
- `POST /api/v1/buddy-reads/{buddy_read_id}/join`
- `POST /api/v1/buddy-reads/{buddy_read_id}/progress`
- `POST /api/v1/readalongs`

Buddy reads are small groups with max participants and per-user progress JSON. Readalongs are larger
hosted reading schedules with optional community linkage and chapter schedule JSON. Dedicated chat
rooms, moderator tools, and announcement feeds are deferred.

## Events, RSVP, Calendar, and Check-In

- `POST /api/v1/events`
- `GET /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `PATCH /api/v1/events/{event_id}`
- `POST /api/v1/events/{event_id}/rsvps`
- `POST /api/v1/events/{event_id}/rsvps/cancel`
- `POST /api/v1/events/{event_id}/checkins`
- `GET /api/v1/events/{event_id}/calendar.ics`

Events support public/private visibility, club/community linkage, IANA time zones, capacity, waitlist
promotion, guest counts, organizer-only check-in codes, and iCalendar export. Capacity changes and
RSVP cancellation promote waiting users in waitlist order when seats are available.
