from __future__ import annotations

from .backend import CronBackend, UserCrontabBackend
from .exceptions import CronDuplicateJobError, CronJobNotFoundError, CronValidationError
from .models import CronJob, CronJobSpec, UpsertResult, UpsertStatus
from .validation import (
    try_validate_job_id,
    validate_command,
    validate_job_id,
    validate_schedule,
)


class CronManager:
    """Application-facing API for managed cron jobs."""

    def __init__(
        self,
        backend: CronBackend | None = None,
        managed_prefix: str | None = None,
    ) -> None:
        self._backend = backend or UserCrontabBackend()
        if managed_prefix is not None:
            validate_job_id(managed_prefix)
        self._managed_prefix = managed_prefix

    def list_jobs(self) -> list[CronJob]:
        return self._backend.list_jobs()

    def list_managed_jobs(self) -> list[CronJob]:
        managed: list[CronJob] = []
        for job in self._backend.list_jobs():
            if not try_validate_job_id(job.job_id).is_valid:
                continue
            if self._managed_prefix and not job.job_id.startswith(self._managed_prefix):
                continue
            managed.append(job)
        return managed

    def get_job(self, job_id: str) -> CronJob:
        self._validate_managed_job_id(job_id)
        matches = self._find_by_job_id(job_id)
        if not matches:
            raise CronJobNotFoundError(f"Cron job not found: {job_id}")
        if len(matches) > 1:
            raise CronDuplicateJobError(
                f"Multiple cron entries found for job_id '{job_id}'"
            )
        return matches[0]

    def exists(self, job_id: str) -> bool:
        self._validate_managed_job_id(job_id)
        matches = self._find_by_job_id(job_id)
        if len(matches) > 1:
            raise CronDuplicateJobError(
                f"Multiple cron entries found for job_id '{job_id}'"
            )
        return len(matches) == 1

    def upsert_job(
        self,
        job_id: str,
        schedule: str,
        command: str,
        enabled: bool = True,
    ) -> UpsertResult:
        spec = CronJobSpec(
            job_id=self._validate_managed_job_id(job_id),
            schedule=validate_schedule(schedule),
            command=validate_command(command),
            enabled=enabled,
        )

        matches = self._find_by_job_id(spec.job_id)
        if len(matches) > 1:
            raise CronDuplicateJobError(
                f"Multiple cron entries found for job_id '{spec.job_id}'"
            )

        if len(matches) == 1:
            existing = matches[0]
            if (
                existing.schedule == spec.schedule
                and existing.command == spec.command
                and existing.enabled == spec.enabled
            ):
                return UpsertResult(status=UpsertStatus.UNCHANGED, job=existing)
            saved = self._backend.save_job(spec)
            return UpsertResult(status=UpsertStatus.UPDATED, job=saved)

        created = self._backend.save_job(spec)
        return UpsertResult(status=UpsertStatus.CREATED, job=created)

    def pause_job(self, job_id: str) -> CronJob:
        job = self.get_job(job_id)
        if not job.enabled:
            return job
        spec = CronJobSpec(
            job_id=job.job_id,
            schedule=job.schedule,
            command=job.command,
            enabled=False,
        )
        return self._backend.save_job(spec)

    def resume_job(self, job_id: str) -> CronJob:
        job = self.get_job(job_id)
        if job.enabled:
            return job
        spec = CronJobSpec(
            job_id=job.job_id,
            schedule=job.schedule,
            command=job.command,
            enabled=True,
        )
        return self._backend.save_job(spec)

    def delete_job(self, job_id: str) -> None:
        self._validate_managed_job_id(job_id)
        matches = self._find_by_job_id(job_id)
        if len(matches) > 1:
            raise CronDuplicateJobError(
                f"Multiple cron entries found for job_id '{job_id}'"
            )
        if not matches:
            return
        self._backend.delete_jobs(job_id)

    def _find_by_job_id(self, job_id: str) -> list[CronJob]:
        return [job for job in self._backend.list_jobs() if job.job_id == job_id]

    def _validate_managed_job_id(self, job_id: str) -> str:
        validated = validate_job_id(job_id)
        if self._managed_prefix and not validated.startswith(self._managed_prefix):
            raise CronValidationError(
                f"job_id must start with managed prefix '{self._managed_prefix}'"
            )
        return validated
