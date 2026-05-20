from cron_manager import CronManager
from cron_manager.backend import FakeBackend
from cron_manager.flask_service import FlaskCronService


def test_flask_service_list_jobs_response() -> None:
    manager = CronManager(backend=FakeBackend(), managed_prefix="my-app:")
    service = FlaskCronService(manager)

    manager.upsert_job(
        job_id="my-app:cleanup",
        schedule="0 3 * * *",
        command="/opt/app/cleanup.sh",
        enabled=True,
    )

    payload, status = service.list_jobs_response()
    assert status == 200
    assert len(payload["jobs"]) == 1
    assert payload["jobs"][0]["job_id"] == "my-app:cleanup"


def test_flask_service_maps_validation_error_to_400() -> None:
    service = FlaskCronService(CronManager(backend=FakeBackend(), managed_prefix="my-app:"))
    payload, status = service.exists_response("other-app:cleanup")

    assert status == 400
    assert "error" in payload


def test_flask_service_maps_not_found_to_404() -> None:
    service = FlaskCronService(CronManager(backend=FakeBackend()))
    payload, status = service.pause_response("missing-job")

    assert status == 404
    assert "error" in payload
