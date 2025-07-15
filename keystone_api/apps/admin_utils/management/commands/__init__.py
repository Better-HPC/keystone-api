class StdOutUtils:
    """Convenience utilities for consistant behavior when writing to STDOUT."""

    def _write(self, message: str, style=None, ending: str = '\n') -> None:
        """Write a message to stdout and immediately flush.

        Args:
            message: The message to write.
            style: Optional style to apply.
            ending: Optional line ending.
        """

        self.stdout.write(message, style, ending=ending)
        self.stdout.flush()
