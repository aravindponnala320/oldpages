# Catalog API

Milestone 2 separates canonical book metadata from future marketplace listings. Public reads return catalog edition IDs; future listings should store the returned `book.id` as their edition reference.

## Public Endpoints

- `GET /api/v1/books`
- `GET /api/v1/books/{book_id}`
- `POST /api/v1/books/resolve-isbn`
- `GET /api/v1/categories`
- `GET /api/v1/authors`
- `GET /api/v1/publishers`

Book list filters:

- `query`
- `isbn`
- `author`
- `category`
- `publisher`
- `language`
- `cursor`
- `limit`

List responses use cursor pagination with stable newest-first ordering.

## Authenticated Metadata Endpoints

- `POST /api/v1/books`
- `PATCH /api/v1/books/{book_id}`

These endpoints are intentionally small admin-correction hooks. Until platform roles are implemented, they require an authenticated active account and write audit rows. Real moderator/admin RBAC should replace this temporary permission rule in the admin milestone.

## ISBN Resolution

`POST /api/v1/books/resolve-isbn` validates ISBN-10/ISBN-13 checksums and resolves against the local catalog provider. The provider interface is isolated so Google Books, Open Library, or a licensed metadata provider can be added later without changing the API contract.

## Duplicate Rules

- ISBN-10 and ISBN-13 values are globally unique.
- Non-ISBN duplicates are detected with an edition fingerprint built from normalized title, authors, publisher, edition, publication year, language, and format.
- Duplicate writes return RFC 7807 problem type `https://oldpages.in/problems/duplicate-catalog-entry`.

## Category Tree

Categories are an adjacency-list tree with nullable `parent_id`, so arbitrary depth is supported. The public category endpoint returns nested nodes.
