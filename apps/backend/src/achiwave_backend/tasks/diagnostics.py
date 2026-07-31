from celery import shared_task


@shared_task(name="achiwave.diagnostics.ping")
def ping() -> dict[str, str]:
    return {"status": "pong"}
