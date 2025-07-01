"""Custom log handlers for use with the builtin Python logging module.

Log handlers manage the distribution of log records to specific destinations
such as files, streams, or sockets. They provide a means to control the output
destination and formatting of log messages within the logging framework.
"""

import logging
from logging import Handler

__all__ = ['DBHandler']


class DBHandler(Handler):
    """Logging handler for storing log records in the application database."""

    def emit(self, record: logging.LogRecord) -> None:
        """Record a log record to the database.

        Args:
            record: The log record to save.
        """

        # Models cannot be imported until Django has loaded the app registry
        from .models import AppLog

        if record.levelno >= self.level:
            AppLog(
                name=record.name,
                level=record.levelname,
                pathname=record.pathname,
                lineno=record.lineno,
                message=self.format(record),
                func=record.funcName,
                sinfo=record.stack_info
            ).save()
