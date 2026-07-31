# Local infrastructure

The local Compose stack runs PostgreSQL, Redis, FastAPI, a Celery worker, and
Celery Beat. The Expo application and Android tooling stay on the host.

From the repository root, create an ignored local environment file:

```powershell
Copy-Item infrastructure/.env.example infrastructure/.env
```

Replace the example PostgreSQL password, then validate and start the stack:

```powershell
docker compose -f infrastructure/compose.local.yaml config
docker compose -f infrastructure/compose.local.yaml up -d --build
docker compose -f infrastructure/compose.local.yaml ps
```

Apply the empty Stage 2 baseline:

```powershell
docker compose -f infrastructure/compose.local.yaml run --rm backend python -m alembic upgrade head
```

FastAPI is available on `http://127.0.0.1:8000`; PostgreSQL and Redis bind only
to the local loopback interface. Containers communicate through the internal
service names `postgres` and `redis`. PostgreSQL uses a named volume and
survives `docker compose stop` followed by `docker compose start`. Redis
persistence is intentionally disabled for this local foundation.

Stop containers without deleting PostgreSQL data:

```powershell
docker compose -f infrastructure/compose.local.yaml down
```

Only delete a volume for an explicitly disposable Compose project. Never use a
broad volume-pruning command.
