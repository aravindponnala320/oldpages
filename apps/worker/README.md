# OldPages Worker

The Milestone 0 worker runs from the API package:

```sh
python -m oldpages_api.worker
```

This directory exists to reserve the monorepo application boundary. The worker is intentionally not a microservice; it shares the API codebase, configuration, database access, logging, and Redis client.
