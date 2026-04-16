"""Custom exceptions raised by the parent application."""

__all__ = ["DryRunRollbackError", "JobExecutionError", "ReferenceResolutionError"]


class JobExecutionError(Exception):
    """Raised when a step inside a batch job fails during execution."""

    def __init__(self, index: int, method: str, path: str, status_code: int, body: dict) -> None:
        """Initialize the exception.

        Args:
            index: The execution index of the step.
            method: The HTTP method executed by the step.
            path: The API endpoint executed by step.
            status_code: The HTTP status code resulting from execution.
            body: The HTTP requesst body executed by the step.
        """

        self.index = index
        self.method = method
        self.path = path
        self.status_code = status_code
        self.body = body
        super().__init__(f'Step #{index} ({method} {path}) failed with status {status_code}')


class ReferenceResolutionError(Exception):
    """Raised when a symbolic reference cannot be resolved."""

    def __init__(self, token: str, reason: str) -> None:
        """Initialize the exception.

        Args:
            token: The token that failed to resolve.
            reason: The reason for execution failure.
        """

        self.token = token
        self.reason = reason
        super().__init__(f'Cannot resolve reference "{token}": {reason}')


class DryRunRollbackError(Exception):
    """Raised to deliberately abort a dry-run transaction."""
