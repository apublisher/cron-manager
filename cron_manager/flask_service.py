from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .exceptions import (
    CronBackendError,
    CronDuplicateJobError,
    CronJobNotFoundError,
    CronValidationError,
)
from .manager import CronManager


class FlaskCronService:
    """Small adapter to simplify CronManager usage from Flask route handlers."""

    def __init__(self, manager: CronManager) -> None:
        self._manager = manager

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> FlaskCronService:
        managed_prefix = config.get("CRON_MANAGER_PREFIX")
        manager = CronManager(managed_prefix=managed_prefix)
        return cls(manager)

    def list_jobs_response(self) -> tuple[dict[str, Any], int]:
        jobs = [asdict(job) for job in self._manager.list_managed_jobs()]
        return {"jobs": jobs}, 200

    def exists_response(self, job_id: str) -> tuple[dict[str, Any], int]:
        try:
            return {"job_id": job_id, "exists": self._manager.exists(job_id)}, 200
        except CronValidationError as exc:
            return {"error": str(exc)}, 400
        except CronDuplicateJobError as exc:
            return {"error": str(exc)}, 409

    def upsert_response(
        self,
        *,
        job_id: str,
        schedule: str,
        command: str,
        enabled: bool,
    ) -> tuple[dict[str, Any], int]:
        try:
            result = self._manager.upsert_job(
                job_id=job_id,
                schedule=schedule,
                command=command,
                enabled=enabled,
            )
        except CronValidationError as exc:
            return {"error": str(exc)}, 400
        except CronDuplicateJobError as exc:
            return {"error": str(exc)}, 409
        except CronBackendError as exc:
            return {"error": str(exc)}, 500

        return {
            "status": result.status.value,
            "job": asdict(result.job),
        }, 200

    def pause_response(self, job_id: str) -> tuple[dict[str, Any], int]:
        return self._toggle_response(action="pause", job_id=job_id)

    def resume_response(self, job_id: str) -> tuple[dict[str, Any], int]:
        return self._toggle_response(action="resume", job_id=job_id)

    def delete_response(self, job_id: str) -> tuple[dict[str, Any], int]:
        try:
            self._manager.delete_job(job_id)
        except CronValidationError as exc:
            return {"error": str(exc)}, 400
        except CronDuplicateJobError as exc:
            return {"error": str(exc)}, 409
        except CronBackendError as exc:
            return {"error": str(exc)}, 500
        return {"deleted": True, "job_id": job_id}, 200

    def _toggle_response(self, *, action: str, job_id: str) -> tuple[dict[str, Any], int]:
        try:
            if action == "pause":
                job = self._manager.pause_job(job_id)
            else:
                job = self._manager.resume_job(job_id)
        except CronValidationError as exc:
            return {"error": str(exc)}, 400
        except CronJobNotFoundError as exc:
            return {"error": str(exc)}, 404
        except CronDuplicateJobError as exc:
            return {"error": str(exc)}, 409
        except CronBackendError as exc:
            return {"error": str(exc)}, 500

        return {"job": asdict(job)}, 200
