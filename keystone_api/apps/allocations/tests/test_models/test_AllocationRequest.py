"""Unit tests for the `AllocationRequest` class."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.allocations.factories import AllocationRequestFactory
from apps.users.factories import TeamFactory


class CleanMethod(TestCase):
    """Test the validation of record data via the `clean` method."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.team = TeamFactory()

    def test_clean_method_valid(self) -> None:
        """Verify the clean method returns successfully when dates are valid."""

        allocation_request = AllocationRequestFactory(
            active='2024-01-01',
            expire='2024-12-31'
        )

        allocation_request.clean()

    def test_clean_method_invalid(self) -> None:
        """Verify the clean method raises a `ValidationError` when active date is after or equal to expire."""

        allocation_request_after = AllocationRequestFactory(
            active='2024-12-31',
            expire='2024-01-01'
        )

        with self.assertRaises(ValidationError):
            allocation_request_after.clean()

        allocation_request_equal = AllocationRequestFactory(
            active='2024-01-01',
            expire='2024-01-01'
        )

        with self.assertRaises(ValidationError):
            allocation_request_equal.clean()


class GetTeamMethod(TestCase):
    """Test the retrieval of a request's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.team = TeamFactory()
        self.allocation_request = AllocationRequestFactory(
            team=self.team
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.allocation_request.get_team())
