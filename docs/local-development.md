# Local development

This guide brings up the Stage 2 mobile, API, PostgreSQL, Redis, Celery worker,
and Celery Beat foundations on Windows with PowerShell. Stage 2 contains no
authentication, progression, or other Stage 3 domain implementation.

## Prerequisites

Install:

- Git;
- Node.js 22 LTS and npm 10 or later;
- Python 3.12;
- Docker Desktop with Linux containers and Docker Compose v2;
- Android Studio with its bundled JDK, an Android SDK platform, Android SDK
  Build-Tools, Android SDK Platform-Tools, and an Android Virtual Device, or a
  physical Android device with USB debugging enabled.

Confirm the command-line tools before setup:

```powershell
git --version
node --version
npm --version
python --version
docker version
docker compose version
adb version
```

Android Studio normally installs the SDK under
`$env:LOCALAPPDATA\Android\Sdk`. If its tools are not already on `PATH`, set the
current PowerShell session:

```powershell
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:Path = "$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\emulator;$env:Path"
$env:JAVA_HOME = "<your Android Studio installation>\jbr"
```

Replace the `JAVA_HOME` placeholder with the actual Android Studio path.

## Clone and configure

Work from an up-to-date feature branch. Do not implement directly on `main`.

```powershell
git clone https://github.com/zidaneyoung/Achiwave.git
Set-Location Achiwave
git switch main
git pull --ff-only
git switch -c <your-feature-branch>
```

Configure and install the mobile package:

```powershell
Set-Location apps\mobile
Copy-Item .env.example .env
npm ci
Set-Location ..\..
```

Configure the backend and create an isolated Python environment:

```powershell
Set-Location apps\backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Set-Location ..\..
```

Replace the disposable PostgreSQL password in `apps/backend/.env` if you also
override `ACHIWAVE_POSTGRES_PASSWORD` for Compose. Real `.env` files are
ignored. Never put secrets in an `EXPO_PUBLIC_*` value because Expo embeds
those values in the application bundle.

## Run backend services

### Entire local stack with Compose

From the repository root:

```powershell
docker compose -f infrastructure\compose.local.yaml up --build -d
docker compose -f infrastructure\compose.local.yaml run --rm backend python -m alembic upgrade head
docker compose -f infrastructure\compose.local.yaml ps
```

The API is available on `http://127.0.0.1:8000`. Check both health contracts:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
Invoke-RestMethod http://127.0.0.1:8000/health/ready
```

Follow structured logs:

```powershell
docker compose -f infrastructure\compose.local.yaml logs -f backend worker scheduler
```

Stop containers without deleting PostgreSQL data:

```powershell
docker compose -f infrastructure\compose.local.yaml down
```

The following reset is **destructive**. It permanently deletes the Compose
project's local PostgreSQL volume:

```powershell
docker compose -f infrastructure\compose.local.yaml down -v
```

### Services and processes in separate terminals

Start only PostgreSQL and Redis:

```powershell
docker compose -f infrastructure\compose.local.yaml up -d postgres redis
```

In `apps/backend`, activate `.venv`, then apply and inspect migrations:

```powershell
python -m alembic upgrade head
python -m alembic current
```

Start the API:

```powershell
python -m uvicorn achiwave_backend.main:app --reload --no-access-log
```

Start a worker in another activated terminal:

```powershell
$env:ACHIWAVE_SERVICE_NAME = "worker"
python -m celery -A achiwave_backend.worker:celery_app worker --loglevel=INFO
```

Start the scheduler in a third activated terminal:

```powershell
$env:ACHIWAVE_SERVICE_NAME = "scheduler"
python -m celery -A achiwave_backend.worker:celery_app beat --loglevel=INFO --schedule .runtime/celerybeat-schedule
```

Stage 2 intentionally has no scheduled domain jobs. The worker includes only a
side-effect-free diagnostic task used to verify broker and worker wiring.

## Run Android

Open an Android Virtual Device in Android Studio, or connect an unlocked
physical device and accept its USB-debugging prompt. Confirm it is visible:

```powershell
adb devices
```

From `apps/mobile`, start Metro for the development client:

```powershell
npx expo start --dev-client
```

In another terminal, build and install the native development app:

```powershell
npx expo run:android
```

For the standard Android emulator, keep:

```dotenv
EXPO_PUBLIC_API_ENV=development
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000
```

`10.0.2.2` is the emulator's route to the development host. It is not the
address for a physical phone.

For a physical device, use the computer's reachable LAN address, for example
`http://192.168.1.20:8000`, and run the API with an explicit LAN bind:

```powershell
python -m uvicorn achiwave_backend.main:app --host 0.0.0.0 --port 8000 --reload --no-access-log
```

Allow only the required private-network firewall access. The checked-in Compose
ports bind to `127.0.0.1` deliberately, so a physical device cannot reach the
Compose API without an intentional local override. USB-connected devices can
use `adb reverse tcp:8081 tcp:8081` for Metro, but API routing still follows the
configured API base URL.

Production config must use `EXPO_PUBLIC_API_ENV=production` and an explicit
HTTPS `EXPO_PUBLIC_API_BASE_URL` without credentials, query parameters, or a
fragment. EAS builds require Expo authentication, project linking, and signing
credentials that are intentionally not committed in Stage 2:

```powershell
npx eas-cli build --platform android --profile development
```

## Verify

Run mobile checks from `apps/mobile`:

```powershell
npm ci
npm run typecheck
npx expo-doctor
npx expo export --platform android --output-dir .stage2-export
```

Remove the generated `.stage2-export` directory after inspection. It is not
source.

Run backend checks from `apps/backend` with `.venv` active:

```powershell
python -m pip check
python -m compileall -q src tests
python -m pytest -q
python -m alembic upgrade head
python -m alembic current
```

Validate Compose from the repository root:

```powershell
docker compose -f infrastructure\compose.local.yaml config --quiet
docker compose -f infrastructure\compose.local.yaml ps
docker compose -f infrastructure\compose.local.yaml logs backend worker scheduler
```

The expected runtime evidence is:

- `/health/live` returns HTTP 200 without consulting dependencies;
- `/health/ready` returns HTTP 200 only when PostgreSQL and Redis both respond,
  and HTTP 503 otherwise;
- an Alembic upgrade reaches the Stage 2 baseline;
- the diagnostic Celery task is consumed by the worker;
- Celery Beat starts with an empty Stage 2 schedule;
- backend, worker, and scheduler application log records are valid JSON and do
  not expose configured credentials or connection URLs.

## Troubleshooting

### npm reports no package or lock file

Run mobile npm commands from `apps/mobile`, not the repository root. Confirm
that both `package.json` and `package-lock.json` are present.

### Android SDK, JDK, or ADB is not found

Open Android Studio's SDK Manager and install an SDK platform, Build-Tools,
Platform-Tools, and an emulator image. Set `ANDROID_HOME`, `JAVA_HOME`, and
`PATH` as shown above, open a new terminal, and re-run `adb version`.

### The emulator or phone cannot reach Metro

Check `adb devices`, keep Metro running, reload the app, and confirm no other
process owns port 8081. For a USB device, try `adb reverse tcp:8081 tcp:8081`.

### The app cannot reach the API

Use `10.0.2.2`, not `localhost`, from the standard Android emulator. Use a
reachable LAN address from a physical device, bind Uvicorn to `0.0.0.0`, and
check the private-network firewall. Re-evaluate Expo config after changing
`.env`; public values are embedded at bundle time.

### Docker does not start

Start Docker Desktop and wait for `docker version` to show both client and
server. Confirm Linux-container mode, virtualization, and WSL 2 integration.
Then run `docker compose -f infrastructure\compose.local.yaml config --quiet`
before retrying the stack.

### PostgreSQL or Redis is unavailable

Inspect `docker compose -f infrastructure\compose.local.yaml ps` and service
logs. Confirm ports 5432 and 6379 are free or override
`ACHIWAVE_POSTGRES_PORT` and `ACHIWAVE_REDIS_PORT` before `docker compose up`.
Keep backend URLs aligned with those overrides.

### Alembic cannot connect or reports the wrong revision

Run from `apps/backend` so `.env` is discovered. Check
`ACHIWAVE_DATABASE_URL`, start PostgreSQL, then run `python -m alembic current`
and `python -m alembic upgrade head`.

### Celery cannot connect or does not consume the diagnostic task

Start Redis first. Confirm `ACHIWAVE_CELERY_BROKER_URL`,
`ACHIWAVE_CELERY_RESULT_BACKEND`, and `ACHIWAVE_REDIS_URL` select the intended
Redis service. Start the worker before dispatching the task.

### A port is already in use

Find the process with `Get-NetTCPConnection -LocalPort <port>` and stop the
specific conflicting process, or set the relevant Compose port override. Do
not terminate unrelated processes broadly.

### Environment values are not loaded

Verify each `.env` is in its package directory. Backend commands should run
from `apps/backend`; Expo commands should run from `apps/mobile`. Restart
long-running processes after changes.

### A command differs between PowerShell and another shell

This guide uses PowerShell syntax: `$env:NAME = "value"`, `Copy-Item`, and
Windows virtual-environment activation. In Bash, use `export NAME=value`, `cp`,
and `source .venv/bin/activate` instead.
