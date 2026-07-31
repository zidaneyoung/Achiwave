# Achiwave backend

The backend is a minimal FastAPI service and shared worker package with the
Stage 3 SQLAlchemy/Alembic data model. It does not contain authentication,
domain endpoints, reward services, recurrence workers, or notification delivery.

Create local settings before starting services:

```powershell
Copy-Item .env.example .env
```

Replace the example database password with the password used by your disposable
local PostgreSQL service. `Settings` loads this `.env` file when commands run
from `apps/backend`. Real `.env` files are ignored and must never be committed.

From this directory, install the package in a Python 3.12 virtual environment:

```powershell
python -m pip install -e ".[dev]"
```

Run the API for local development:

```powershell
python -m uvicorn achiwave_backend.main:app --reload --no-access-log
```

The process-only liveness endpoint is `GET /health/live`. The dependency-aware
readiness endpoint is `GET /health/ready` and returns HTTP 503 until both
PostgreSQL and Redis are reachable.

Backend, worker, and scheduler logs are JSON lines on standard output. Set
`ACHIWAVE_SERVICE_NAME` to `backend`, `worker`, or `scheduler` when starting
each process outside Compose.

Start the Celery worker after configuring Redis:

```powershell
python -m celery -A achiwave_backend.worker:celery_app worker --loglevel=INFO
```

Start Celery Beat with an explicitly ignored local schedule file:

```powershell
python -m celery -A achiwave_backend.worker:celery_app beat --loglevel=INFO --schedule .runtime/celerybeat-schedule
```

Stage 2 intentionally configures no scheduled domain jobs.

Apply the linear Stage 3 migration chain from this directory:

```powershell
python -m alembic upgrade head
```

Inspect it with `python -m alembic heads`, `python -m alembic current`, and
`python -m alembic check`. The schema and its acceptance evidence are documented
in [`docs/database/stage-3-schema.md`](../../docs/database/stage-3-schema.md) and
[`docs/testing/stage-3-acceptance.md`](../../docs/testing/stage-3-acceptance.md).

The destructive migration tests require an explicitly disposable PostgreSQL URL:

```powershell
$env:ACHIWAVE_TEST_DATABASE_URL = '<explicit disposable PostgreSQL URL>'
python -m pytest tests/test_stage3_postgres.py -q
```

The tests refuse database names that do not contain `test`, `stage3`, or `ci`.
