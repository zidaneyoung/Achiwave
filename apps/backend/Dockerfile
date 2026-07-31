FROM python:3.12.13-slim-bookworm

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations

RUN python -m pip install . \
    && addgroup --system achiwave \
    && adduser --system --ingroup achiwave achiwave \
    && mkdir -p /app/.runtime \
    && chown -R achiwave:achiwave /app

USER achiwave

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "achiwave_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
