from __future__ import annotations

from typing import Protocol

from .exceptions import CronBackendError
from .models import CronJob, CronJobSpec


class CronBackend(Protocol):
    def list_jobs(self) -> list[CronJob]:
        ...

    def save_job(self, spec: CronJobSpec) -> CronJob:
        ...

    def delete_jobs(self, job_id: str) -> int:
        ...


class FakeBackend:
    """In-memory backend for tests and local development."""

    def __init__(self, jobs: list[CronJob] | None = None) -> None:
        self._jobs: list[CronJob] = list(jobs or [])

    def list_jobs(self) -> list[CronJob]:
        return list(self._jobs)

    def save_job(self, spec: CronJobSpec) -> CronJob:
        job = CronJob(
            job_id=spec.job_id,
            schedule=spec.schedule,
            command=spec.command,
            enabled=spec.enabled,
        )
        for idx, existing in enumerate(self._jobs):
            if existing.job_id == spec.job_id:
                self._jobs[idx] = job
                return job
        self._jobs.append(job)
        return job

    def delete_jobs(self, job_id: str) -> int:
        original_count = len(self._jobs)
        self._jobs = [job for job in self._jobs if job.job_id != job_id]
        return original_count - len(self._jobs)


class UserCrontabBackend:
    """Linux user crontab backend based on python-crontab."""

    def __init__(self) -> None:
        try:
            from crontab import CronTab
        except Exception as exc:  # pragma: no cover - import environment issue
            raise CronBackendError(
                "python-crontab is required for UserCrontabBackend"
            ) from exc

        self._cron = CronTab(user=True)

    def list_jobs(self) -> list[CronJob]:
        jobs: list[CronJob] = []
        for item in self._cron:
            jobs.append(
                CronJob(
                    job_id=(item.comment or "").strip(),
                    schedule=str(item.slices),
                    command=str(item.command),
                    enabled=item.is_enabled(),
                )
            )
        return jobs

    def save_job(self, spec: CronJobSpec) -> CronJob:
        matches = list(self._cron.find_comment(spec.job_id))

        if not matches:
            item = self._cron.new(command=spec.command, comment=spec.job_id)
            item.setall(spec.schedule)
            item.enable(spec.enabled)
            self._write()
            return CronJob(
                job_id=spec.job_id,
                schedule=spec.schedule,
                command=spec.command,
                enabled=spec.enabled,
            )

        if len(matches) > 1:
            raise CronBackendError(
                f"Multiple cron entries found for job_id '{spec.job_id}'"
            )

        item = matches[0]
        item.setall(spec.schedule)
        item.set_command(spec.command)
        item.enable(spec.enabled)
        self._write()

        return CronJob(
            job_id=spec.job_id,
            schedule=spec.schedule,
            command=spec.command,
            enabled=spec.enabled,
        )

    def delete_jobs(self, job_id: str) -> int:
        removed = self._cron.remove_all(comment=job_id)
        if removed:
            self._write()
        return int(removed)

    def _write(self) -> None:
        try:
            self._cron.write()
        except Exception as exc:
            raise CronBackendError("Failed to write user crontab") from exc
