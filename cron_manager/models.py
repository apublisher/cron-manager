from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class CronJob:
    """Represents one cron entry as exposed by the application API."""

    job_id: str
    schedule: str
    command: str
    enabled: bool


@dataclass(frozen=True)
class CronJobSpec:
    """Input payload used to create or update a managed cron job."""

    job_id: str
    schedule: str
    command: str
    enabled: bool = True


class UpsertStatus(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class UpsertResult:
    status: UpsertStatus
    job: CronJob
