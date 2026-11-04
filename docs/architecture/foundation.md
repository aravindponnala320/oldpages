# Milestone 0 Foundation

Milestone 0 establishes the repository, local services, API shell, browser shells, CI, and test harness. It deliberately avoids product domains such as identity, catalog, listings, chat, payments, and communities.

## Runtime Shape

```text
Browser apps
  |-- apps/web
  |-- apps/admin
       |
       v
FastAPI modular monolith
  |-- apps/api
  |-- apps/api worker process
       |
       |-- PostgreSQL + PostGIS
       |-- Redis
       |-- MinIO
```

The API and worker use the same application package. The worker is a separate process for asynchronous work, not a separate service boundary.

## API Foundation

- Application factory: `oldpages_api.main:create_app`
- Configuration: `oldpages_api.core.config.Settings`
- Request ID middleware: every response carries `X-Request-ID`
- Error handling: RFC 7807-style JSON problem details
- Logging: JSON records with request IDs
- Tracing: OpenTelemetry FastAPI instrumentation hook, disabled by default locally
- Health:
  - `GET /health/live`
  - `GET /health/ready`
- Example endpoint:
  - `GET /api/v1/foundation/example`

## Database Foundation

Alembic migration `0001_foundation` creates:

- `postgis` extension
- `pgcrypto` extension
- `outbox_events` table for future transactional domain events

The rollback drops only the table and indexes. Extensions are left installed because dropping shared database extensions can be unsafe in multi-tenant or reused local databases.

## Local Infrastructure

`docker compose up --build` starts:

- PostgreSQL with PostGIS
- Redis
- MinIO object-storage emulator
- API
- Worker
- Web shell
- Admin shell

## Test Strategy

Milestone 0 tests cover:

- Configuration parsing
- Public ID generation
- Health endpoints
- Dependency readiness behavior
- One API example endpoint end to end
- API client parsing
- Web/admin shell rendering
- Playwright smoke tests for web/admin shells

Later milestones must add domain-level service, repository, authorization, state-machine, and integration tests as each module is introduced.
