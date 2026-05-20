import pytest

from cron_manager import (
    CronDuplicateJobError,
    CronJob,
    CronJobNotFoundError,
    CronManager,
    CronValidationError,
)
from cron_manager.backend import FakeBackend
from cron_manager.models import UpsertStatus


def test_upsert_create_update_unchanged_and_delete() -> None:
    backend = FakeBackend()
    manager = CronManager(backend=backend)

    created = manager.upsert_job(
        job_id="my-app:nightly-import",
        schedule="0 2 * * *",
        command="/opt/app/run-import.sh",
        enabled=True,
    )
    assert created.status == UpsertStatus.CREATED

    unchanged = manager.upsert_job(
        job_id="my-app:nightly-import",
        schedule="0 2 * * *",
        command="/opt/app/run-import.sh",
        enabled=True,
    )
    assert unchanged.status == UpsertStatus.UNCHANGED

    updated = manager.upsert_job(
        job_id="my-app:nightly-import",
        schedule="5 2 * * *",
        command="/opt/app/run-import.sh",
        enabled=False,
    )
    assert updated.status == UpsertStatus.UPDATED
    assert updated.job.enabled is False

    manager.delete_job("my-app:nightly-import")
    assert manager.exists("my-app:nightly-import") is False


def test_pause_resume_are_idempotent() -> None:
    backend = FakeBackend(
        jobs=[
            CronJob(
                job_id="my-app:sync",
                schedule="*/10 * * * *",
                command="/opt/app/sync.sh",
                enabled=True,
            )
        ]
    )
    manager = CronManager(backend=backend)

    paused = manager.pause_job("my-app:sync")
    assert paused.enabled is False
    paused_again = manager.pause_job("my-app:sync")
    assert paused_again.enabled is False

    resumed = manager.resume_job("my-app:sync")
    assert resumed.enabled is True
    resumed_again = manager.resume_job("my-app:sync")
    assert resumed_again.enabled is True


def test_get_job_not_found_raises() -> None:
    manager = CronManager(backend=FakeBackend())
    with pytest.raises(CronJobNotFoundError):
        manager.get_job("missing-job")


def test_duplicate_entries_raise_error() -> None:
    manager = CronManager(
        backend=FakeBackend(
            jobs=[
                CronJob("dup-job", "0 1 * * *", "echo one", True),
                CronJob("dup-job", "0 2 * * *", "echo two", True),
            ]
        )
    )

    with pytest.raises(CronDuplicateJobError):
        manager.exists("dup-job")

    with pytest.raises(CronDuplicateJobError):
        manager.upsert_job("dup-job", "0 1 * * *", "echo one")


def test_list_managed_jobs_filters_invalid_job_ids() -> None:
    manager = CronManager(
        backend=FakeBackend(
            jobs=[
                CronJob("good:job", "0 1 * * *", "echo ok", True),
                CronJob("", "0 1 * * *", "echo empty", True),
                CronJob("!bad", "0 1 * * *", "echo bad", True),
            ]
        )
    )

    jobs = manager.list_managed_jobs()
    assert [job.job_id for job in jobs] == ["good:job"]


def test_list_managed_jobs_filters_by_prefix() -> None:
    manager = CronManager(
        backend=FakeBackend(
            jobs=[
                CronJob("my-app:job-one", "0 1 * * *", "echo one", True),
                CronJob("other-app:job-two", "0 1 * * *", "echo two", True),
                CronJob("!invalid", "0 1 * * *", "echo bad", True),
            ]
        ),
        managed_prefix="my-app:",
    )

    jobs = manager.list_managed_jobs()
    assert [job.job_id for job in jobs] == ["my-app:job-one"]


def test_prefix_policy_enforced_on_write_operations() -> None:
    manager = CronManager(backend=FakeBackend(), managed_prefix="my-app:")

    with pytest.raises(CronValidationError):
        manager.upsert_job(
            job_id="other-app:job",
            schedule="0 1 * * *",
            command="/opt/app/job.sh",
            enabled=True,
        )


def test_prefix_policy_enforced_on_read_operations() -> None:
    manager = CronManager(backend=FakeBackend(), managed_prefix="my-app:")

    with pytest.raises(CronValidationError):
        manager.exists("other-app:job")
