import pytest

from cron_manager.exceptions import CronValidationError
from cron_manager.validation import validate_command, validate_job_id, validate_schedule


def test_validate_job_id_accepts_valid_value() -> None:
    assert validate_job_id("my-app:nightly-import") == "my-app:nightly-import"


@pytest.mark.parametrize("value", ["", " bad", "!bad", "bad\nnext"])
def test_validate_job_id_rejects_invalid_values(value: str) -> None:
    with pytest.raises(CronValidationError):
        validate_job_id(value)


def test_validate_schedule_accepts_5_fields() -> None:
    assert validate_schedule("0 2 * * *") == "0 2 * * *"


@pytest.mark.parametrize("value", ["", "@daily", "0 2 * *", "0 2 * * * *"])
def test_validate_schedule_rejects_non_5_fields(value: str) -> None:
    with pytest.raises(CronValidationError):
        validate_schedule(value)


@pytest.mark.parametrize("value", ["", "echo hi\nrm -rf /", "echo hi\rbye"])
def test_validate_command_rejects_invalid_values(value: str) -> None:
    with pytest.raises(CronValidationError):
        validate_command(value)
