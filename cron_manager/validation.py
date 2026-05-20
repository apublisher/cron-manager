from __future__ import annotations

import re

from .exceptions import CronValidationError

JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")


class ValidationResult:
    """Simple helper for optional validation flows."""

    __slots__ = ("is_valid", "reason")

    def __init__(self, is_valid: bool, reason: str | None = None) -> None:
        self.is_valid = is_valid
        self.reason = reason


def validate_job_id(job_id: str) -> str:
    if not job_id:
        raise CronValidationError("job_id is required")
    if not JOB_ID_PATTERN.fullmatch(job_id):
        raise CronValidationError(
            "job_id must match regex: ^[A-Za-z0-9][A-Za-z0-9._:/-]*$"
        )
    return job_id


def try_validate_job_id(job_id: str) -> ValidationResult:
    try:
        validate_job_id(job_id)
    except CronValidationError as exc:
        return ValidationResult(False, str(exc))
    return ValidationResult(True)


def validate_command(command: str) -> str:
    if not command:
        raise CronValidationError("command is required")
    if "\n" in command or "\r" in command:
        raise CronValidationError("command must be a single line")
    return command


def validate_schedule(schedule: str) -> str:
    parts = schedule.split()
    if len(parts) != 5:
        raise CronValidationError("schedule must contain exactly 5 cron fields")
    return schedule
