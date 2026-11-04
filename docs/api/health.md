# Health API

## `GET /health/live`

Returns process liveness. This endpoint does not check external dependencies.

Example response:

```json
{
  "components": {},
  "environment": "local",
  "service": "oldpages-api",
  "status": "ok",
  "version": "0.0.0"
}
```

## `GET /health/ready`

Checks PostgreSQL and Redis. Returns `200` when all dependencies are available and `503` when any dependency fails.

Example response:

```json
{
  "components": {
    "database": { "status": "ok", "detail": null },
    "redis": { "status": "ok", "detail": null }
  },
  "environment": "local",
  "service": "oldpages-api",
  "status": "ok",
  "version": "0.0.0"
}
```

All responses include the `X-Request-ID` header.
