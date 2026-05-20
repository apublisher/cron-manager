class CronManagerError(Exception):
    """Base exception for all cron manager errors."""


class CronValidationError(CronManagerError):
    """Raised when user input fails validation."""


class CronJobNotFoundError(CronManagerError):
    """Raised when a managed cron job cannot be found."""


class CronBackendError(CronManagerError):
    """Raised when the backend cannot complete an operation."""


class CronDuplicateJobError(CronManagerError):
    """Raised when multiple jobs share the same job identifier."""
