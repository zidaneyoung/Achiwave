from pathlib import Path

from achiwave_backend.config import Settings
from achiwave_backend.worker import create_celery_app


def test_scheduler_has_no_domain_schedule() -> None:
    settings = Settings(
        _env_file=None,
        celery_beat_schedule_filename=".runtime/test-celerybeat-schedule",
    )

    application = create_celery_app(settings)

    assert application.conf.beat_schedule == {}
    assert Path(application.conf.beat_schedule_filename) == Path(
        ".runtime/test-celerybeat-schedule"
    )
