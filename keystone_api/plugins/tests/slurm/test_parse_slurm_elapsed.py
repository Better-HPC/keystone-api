"""Unit tests for the `parse_slurm_elapsed` function."""

import unittest
from datetime import timedelta

from plugins.slurm import parse_slurm_elapsed


class ParseSlurmElapsedMethod(unittest.TestCase):
    """Test the parsing of slurm elapsed time values."""

    def test_valid_elapsed_with_days(self) -> None:
        """Verify a valid elapsed string with days (D-HH:MM:SS) parses correctly."""

        elapsed_str = '2-10:15:30'
        expected = timedelta(days=2, hours=10, minutes=15, seconds=30)
        result = parse_slurm_elapsed(elapsed_str)
        self.assertEqual(expected, result)

    def test_valid_elapsed_without_days_hms(self) -> None:
        """Verify a valid elapsed string without days (HH:MM:SS) parses correctly."""

        elapsed_str = '05:45:10'
        expected = timedelta(hours=5, minutes=45, seconds=10)
        result = parse_slurm_elapsed(elapsed_str)
        self.assertEqual(expected, result)

    def test_valid_elapsed_without_days_hm(self) -> None:
        """Verify a valid elapsed string without seconds (HH:MM) parses correctly."""

        elapsed_str = '12:30'
        expected = timedelta(hours=12, minutes=30, seconds=0)
        result = parse_slurm_elapsed(elapsed_str)
        self.assertEqual(expected, result)

    def test_invalid_format(self) -> None:
        """Verify an invalid value `None`."""

        elapsed_str = 'invalid-time'
        result = parse_slurm_elapsed(elapsed_str)
        self.assertIsNone(result)

    def test_empty_string(self) -> None:
        """Verify an empty string returns `None`."""

        result = parse_slurm_elapsed('')
        self.assertIsNone(result)
