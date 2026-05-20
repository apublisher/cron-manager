import json

import cron_manager.cli as cli
import pytest
from cron_manager import CronBackendError, CronJobNotFoundError, CronValidationError
from cron_manager.models import CronJob, UpsertResult, UpsertStatus


class DummyManager:
    def list_managed_jobs(self) -> list[CronJob]:
        return []

    def get_job(self, job_id: str) -> CronJob:
        raise AssertionError("not used")

    def exists(self, job_id: str) -> bool:
        raise AssertionError("not used")

    def upsert_job(
        self,
        job_id: str,
        schedule: str,
        command: str,
        enabled: bool = True,
    ) -> UpsertResult:
        raise AssertionError("not used")

    def pause_job(self, job_id: str) -> CronJob:
        raise AssertionError("not used")

    def resume_job(self, job_id: str) -> CronJob:
        raise AssertionError("not used")

    def delete_job(self, job_id: str) -> None:
        raise AssertionError("not used")


def test_cli_list_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "CronManager", lambda: DummyManager())
    exit_code = cli.main(["--json", "list"])

    assert exit_code == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload == []


class UpsertManager(DummyManager):
    def upsert_job(
        self,
        job_id: str,
        schedule: str,
        command: str,
        enabled: bool = True,
    ) -> UpsertResult:
        return UpsertResult(
            status=UpsertStatus.CREATED,
            job=CronJob(
                job_id=job_id,
                schedule=schedule,
                command=command,
                enabled=enabled,
            ),
        )


def test_cli_upsert_json_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "CronManager", lambda: UpsertManager())
    exit_code = cli.main(
        [
            "--json",
            "upsert",
            "--id",
            "my-app:test",
            "--schedule",
            "0 1 * * *",
            "--command",
            "/opt/app/test.sh",
            "--enabled",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "created"
    assert payload["job"]["job_id"] == "my-app:test"


class ValidationErrorManager(DummyManager):
    def exists(self, job_id: str) -> bool:
        raise CronValidationError("invalid job id")


def test_cli_validation_error_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "CronManager", lambda: ValidationErrorManager())
    exit_code = cli.main(["exists", "bad"])
    assert exit_code == 2


class NotFoundManager(DummyManager):
    def get_job(self, job_id: str) -> CronJob:
        raise CronJobNotFoundError("missing")


def test_cli_not_found_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "CronManager", lambda: NotFoundManager())
    exit_code = cli.main(["get", "my-app:missing"])
    assert exit_code == 3


class BackendErrorManager(DummyManager):
    def delete_job(self, job_id: str) -> None:
        raise CronBackendError("backend failed")


def test_cli_backend_error_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "CronManager", lambda: BackendErrorManager())
    exit_code = cli.main(["delete", "my-app:job"])
    assert exit_code == 4
