from achiwave_backend.config import Settings
from achiwave_backend.worker import create_celery_app


def test_celery_worker_uses_environment_backed_redis_urls() -> None:
    settings = Settings(
        _env_file=None,
        celery_broker_url="redis://broker:6379/1",
        celery_result_backend="redis://results:6379/2",
        celery_task_always_eager=True,
    )

    application = create_celery_app(settings)

    assert application.conf.broker_url == "redis://broker:6379/1"
    assert application.conf.result_backend == "redis://results:6379/2"
    assert application.conf.broker_connection_max_retries == 5
    assert application.conf.task_serializer == "json"


def test_diagnostic_task_is_discoverable_and_executes() -> None:
    settings = Settings(_env_file=None, celery_task_always_eager=True)
    application = create_celery_app(settings)

    application.loader.import_default_modules()
    diagnostic_task = application.tasks["achiwave.diagnostics.ping"]
    result = diagnostic_task.apply()

    assert result.successful()
    assert result.get() == {"status": "pong"}
