# Local Development

## Setup

```sh
cp .env.example .env
make setup
```

## Start Services

```sh
make up
```

Service URLs:

- API: `http://localhost:8000`
- Web: `http://localhost:3000`
- Admin: `http://localhost:3001`
- MinIO console: `http://localhost:9001`

## Database

Apply migrations:

```sh
make migrate
```

Seed demo users, catalog data, one active listing, a sample accepted chat, a pending offer, a
sample trust report, the public `Pune Readers` community, a linked sample club/event, and demo
reading progress/notes/goals/statistics:

```sh
make seed
```

The demo seller is `demo@oldpages.in`, the demo buyer is `buyer@oldpages.in`, and the demo
moderator is `moderator@oldpages.in`. All use `OldPagesDemo!2026` locally.

## Checks

```sh
make lint
make typecheck
make test
make e2e
```

The root Makefile expects `make setup` to create `.venv` and install npm workspaces.
