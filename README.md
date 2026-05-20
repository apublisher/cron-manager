# cron-manager

A small, framework-agnostic Python package for managing Linux user cron jobs with a typed application API and an optional CLI.

## Features

- Read and list cron jobs
- Create or update managed jobs by stable job identifier
- Pause and resume jobs
- Delete jobs
- Idempotent manager operations
- Backend abstraction with in-memory fake backend for tests
- CLI support for direct terminal usage
- Optional managed prefix policy for app job isolation
- Flask-friendly service adapter (without hard Flask dependency)

## Installation

```bash
pip install -e .
```

Install development dependencies:

```bash
pip install -e .[dev]
```

## Quick Start (Python API)

```python
from cron_manager import CronManager

manager = CronManager(managed_prefix="my-app:")

result = manager.upsert_job(
    job_id="my-app:nightly-import",
    schedule="0 2 * * *",
    command="/home/app/.venv/bin/python /home/app/jobs/nightly_import.py",
    enabled=True,
)

print(result.status.value)
print(manager.exists("my-app:nightly-import"))
```

## Managed Prefix Policy

Use `managed_prefix` to isolate your application jobs from unrelated crontab entries.

```python
from cron_manager import CronManager

manager = CronManager(managed_prefix="my-app:")
jobs = manager.list_managed_jobs()  # only job_id values starting with my-app:
```

If `managed_prefix` is configured, read/write operations reject `job_id` values that do not start with the prefix.

## CLI

After installation, the CLI command is available:

```bash
cron-manager --help
```

Commands:

- `list`
- `get <job_id>`
- `exists <job_id>`
- `upsert --id <job_id> --schedule "<cron expr>" --command "<shell cmd>" [--enabled|--disabled]`
- `pause <job_id>`
- `resume <job_id>`
- `delete <job_id>`

Use `--json` for machine-friendly output.

Exit codes:

- `0` success
- `2` validation error
- `3` job not found
- `4` backend or duplicate-job error

Examples:

```bash
cron-manager --json list
cron-manager upsert --id my-app:nightly-import --schedule "0 2 * * *" --command "/opt/app/run.sh" --enabled
cron-manager pause my-app:nightly-import
```

## Validation Rules

- `job_id` must match: `^[A-Za-z0-9][A-Za-z0-9._:/-]*$`
- `schedule` must contain exactly 5 fields
- `command` must be non-empty and single-line

## Testing

Tests use `FakeBackend` and do not modify a real crontab.

```bash
pytest
```

## Security Notes

- Do not pass untrusted shell commands directly from end users.
- Prefer whitelisted command templates.
- Use absolute command paths.
- Consider wrapping commands with `flock` to avoid overlapping runs.

## Flask Integration

The package includes `FlaskCronService` to simplify mapping manager errors to HTTP responses in Flask handlers.

```python
from cron_manager import FlaskCronService

service = FlaskCronService.from_config({"CRON_MANAGER_PREFIX": "my-app:"})
payload, status_code = service.list_jobs_response()
```

See [examples/flask_admin_example.py](examples/flask_admin_example.py) for a full Blueprint example.
