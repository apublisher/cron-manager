# VS Code Agent Prompt: Linux Cron Manager Python Package

## Role

You are a senior Python package architect.

Build a production-quality Python package for managing Linux user crontabs programmatically. The package must be framework-agnostic, strictly typed, well tested, and suitable for later integration into a Flask admin UI.

All source code, comments, docstrings, tests, README content, and examples must be written in English.

---

## Mission

Create a Python package that can read, create, update, enable, disable, and delete Linux cron jobs using a clean, stable application-level API.

The package should wrap `python-crontab`:

```python
from crontab import CronTab
```

The package must not expose `python-crontab` details to package consumers. The public API should be domain-oriented and safe to use from application code.

---

## Primary Use Case

The package will be used from an admin interface in a Flask application where an administrator can:

* list registered cron jobs
* see whether a known cron job exists
* create a cron job
* update its schedule or command
* pause/disable a cron job
* resume/enable a cron job
* delete a cron job
* avoid creating duplicates

The package itself must not depend on Flask.

---

## Design Philosophy

Keep the package small, clean, and practical.

Avoid overengineering, but design it so that the cron backend is isolated behind an interface. The initial implementation should use Linux user crontab via `python-crontab`, but the design should allow a future backend.

Prioritize:

* correctness
* idempotency
* strict typing
* explicit error handling
* safe defaults
* high readability
* predictable behavior
* good testability

---

## Runtime Compatibility

Support Python:

* 3.10
* 3.11
* 3.12

The code must be compatible with VS Code/Pylance strict type checking.

---

## Dependency

Use `python-crontab` as the Linux cron backend dependency.

---

## Public API Overview

```python
manager = CronManager()

jobs = manager.list_jobs()

job = manager.get_job("my-app:nightly-import")

result = manager.upsert_job(
    job_id="my-app:nightly-import",
    schedule="0 2 * * *",
    command="/home/app/.venv/bin/python /home/app/jobs/nightly_import.py",
    enabled=True,
)

manager.pause_job("my-app:nightly-import")
manager.resume_job("my-app:nightly-import")
manager.delete_job("my-app:nightly-import")
```

---

## Identity Strategy

Each managed cron job must have a stable `job_id`, stored in the cron comment field.

This is the primary key.

---

## Core Models

```python
@dataclass(frozen=True)
class CronJob:
    job_id: str
    schedule: str
    command: str
    enabled: bool
```

```python
@dataclass(frozen=True)
class CronJobSpec:
    job_id: str
    schedule: str
    command: str
    enabled: bool = True
```

```python
class UpsertStatus(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
```

```python
@dataclass(frozen=True)
class UpsertResult:
    status: UpsertStatus
    job: CronJob
```

---

## Required API

Implement `CronManager` with:

* list_jobs()
* list_managed_jobs()
* get_job()
* exists()
* upsert_job()
* pause_job()
* resume_job()
* delete_job()

All operations must be idempotent.

---

## Backend Abstraction

Introduce a backend interface (Protocol).

Implement:

* UserCrontabBackend
* FakeBackend (for testing)

---

## Validation Rules

### job_id

* required
* regex: `^[A-Za-z0-9][A-Za-z0-9._:/-]*$`

### schedule

* must be valid cron expression (5 fields)

### command

* must be non-empty
* no newline

---

## Exceptions

```python
class CronManagerError(Exception):
    pass

class CronValidationError(CronManagerError):
    pass

class CronJobNotFoundError(CronManagerError):
    pass

class CronBackendError(CronManagerError):
    pass

class CronDuplicateJobError(CronManagerError):
    pass
```

---

## Duplicate Handling

* job_id is the only primary identifier
* multiple matches must raise error

---

## Testing

Use pytest.

Do NOT modify real crontab.

Use FakeBackend.

Test:

* validation
* create/update/delete
* idempotency
* duplicates

---

## Project Structure

```
cron_manager/
    __init__.py
    manager.py
    models.py
    backend.py
    validation.py
    exceptions.py

tests/
README.md
pyproject.toml
```

---

## Security Notes

* Do not allow untrusted shell commands
* Prefer whitelisted commands
* Use absolute paths
* Recommend flock for locking

---

## Acceptance Criteria

* fully typed
* idempotent
* tested
* backend isolated
* no real cron writes in tests

---

## Implementation Order

1. skeleton
2. exceptions
3. models
4. validation
5. backend
6. fake backend
7. manager
8. real backend
9. tests
10. README

---

## Final Instruction

Adapt to existing repository structure. Do not overwrite useful code. Prefer simple, correct solutions over complex ones.
