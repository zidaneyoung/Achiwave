from celery import Celery

from achiwave_backend.config import Settings, get_settings


def create_celery_app(settings: Settings | None = None) -> Celery:
    resolved_settings = settings or get_settings()
    application = Celery(
        "achiwave",
        broker=resolved_settings.resolved_celery_broker_url(),
        backend=resolved_settings.resolved_celery_result_backend(),
        include=["achiwave_backend.tasks.diagnostics"],
    )
    application.conf.update(
        accept_content=["json"],
        broker_connection_max_retries=5,
        broker_connection_retry_on_startup=True,
        broker_connection_timeout=resolved_settings.redis_connect_timeout_seconds,
        broker_transport_options={
            "socket_connect_timeout": (
                resolved_settings.redis_connect_timeout_seconds
            ),
            "socket_timeout": resolved_settings.redis_socket_timeout_seconds,
            "visibility_timeout": 3600,
        },
        beat_schedule={},
        beat_schedule_filename=str(
            resolved_settings.celery_beat_schedule_filename
        ),
        enable_utc=True,
        result_expires=3600,
        result_serializer="json",
        task_always_eager=resolved_settings.celery_task_always_eager,
        task_default_queue="achiwave",
        task_serializer="json",
        timezone="UTC",
    )
    return application


celery_app = create_celery_app()
