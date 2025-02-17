"""Unit tests for the `DBHandler` class."""

import logging

from django.test import TestCase

from apps.logging.handlers import DBHandler
from apps.logging.models import AppLog


class EmitMethod(TestCase):
    """Test the `emit` method properly records log data in the application database."""

    def assert_db_record_matches_log_content(
        self, handler: logging.Handler, log_record: logging.LogRecord, db_record: AppLog
    ) -> None:
        """Assert the content of a database record matches the content of a log record.

        Args:
            handler: The logging record used to format the log record.
            log_record: The log record.
            db_record: The database record.
        """

        self.assertEqual(db_record.name, log_record.name)
        self.assertEqual(db_record.level, log_record.levelname)
        self.assertEqual(db_record.pathname, log_record.pathname)
        self.assertEqual(db_record.lineno, log_record.lineno)
        self.assertEqual(db_record.message, handler.format(log_record))
        self.assertEqual(db_record.func, log_record.funcName)
        self.assertEqual(db_record.sinfo, log_record.stack_info)

    def test_record_above_logging_threshold(self) -> None:
        """Verify log data is saved when the log message level is above the logging threshold."""

        log_record = logging.LogRecord('test', logging.INFO, 'pathname', 1, 'message', (), None, 'func')
        handler = DBHandler()
        handler.emit(log_record)

        db_record = AppLog.objects.first()
        self.assertEqual(AppLog.objects.count(), 1)
        self.assert_db_record_matches_log_content(handler, log_record, db_record)

    def test_record_equal_logging_threshold(self) -> None:
        """Verify log data is saved when the log message level is equal to the logging threshold."""

        log_record = logging.LogRecord('test', logging.INFO, 'pathname', 1, 'message', (), None, 'func')
        handler = DBHandler(logging.INFO)
        handler.emit(log_record)

        db_record = AppLog.objects.first()
        self.assertEqual(AppLog.objects.count(), 1)
        self.assert_db_record_matches_log_content(handler, log_record, db_record)

    def test_record_below_logging_threshold(self) -> None:
        """Verify log data is not saved when the log message level is below the logging threshold."""

        record = logging.LogRecord('test', logging.INFO, 'pathname', 1, 'message', (), None, 'func')
        handler = DBHandler(level=logging.ERROR)
        handler.emit(record)

        self.assertFalse(AppLog.objects.count())
