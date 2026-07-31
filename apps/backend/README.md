# Achiwave backend

The Stage 2 backend is a minimal FastAPI service and shared worker package. It
does not contain authentication, domain endpoints, or Stage 3 data models.

From this directory, install the package in a Python 3.12 virtual environment:

```powershell
python -m pip install -e ".[dev]"
```

Run the API for local development:

```powershell
python -m uvicorn achiwave_backend.main:app --reload
```

Start the Celery worker after configuring Redis:

```powershell
python -m celery -A achiwave_backend.worker:celery_app worker --loglevel=INFO
```
