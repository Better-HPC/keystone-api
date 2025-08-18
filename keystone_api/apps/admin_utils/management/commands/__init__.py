from django.core.management.base import OutputWrapper


class StdOutUtils:
    """Convenience utilities for consistent behavior when writing to STDOUT."""

    stdout: OutputWrapper

    def _write(self, message: str, style=None, ending: str = '\n') -> None:
        """Write a message to stdout and immediately flush.

        Args:
            message: The message to write.
            style: Optional style to apply.
            ending: Optional line ending.
        """

        self.stdout.write(message, style, ending=ending)
        self.stdout.flush()
