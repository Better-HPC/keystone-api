"""Unit tests for the `parse_slurm_date` function."""

import unittest
from datetime import datetime

from plugins.slurm import parse_slurm_date


class ParseSlurmDateMethod(unittest.TestCase):
    """Test the parsing of slurm date values."""

    def test_valid_date(self) -> None:
        """Verify a valid datetime string parses correctly."""

        date_str = '2025-06-23T14:30:45'
        expected = datetime(2025, 6, 23, 14, 30, 45).astimezone()
        result = parse_slurm_date(date_str)
        self.assertEqual(expected, result)

    def test_invalid_date_format(self):
        """Verify an invalid datetime format returns `None`."""

        date_str = '2025/06/23 14:30:45'
        result = parse_slurm_date(date_str)
        self.assertIsNone(result)

    def test_invalid_date_value(self):
        """Verify parsing an invalid datetime value returns `None`."""

        date_str = "invalid-date-string"
        result = parse_slurm_date(date_str)
        self.assertIsNone(result)

    def test_empty_string(self):
        """Verify parsing an empty string returns `None`."""

        result = parse_slurm_date('')
        self.assertIsNone(result)
