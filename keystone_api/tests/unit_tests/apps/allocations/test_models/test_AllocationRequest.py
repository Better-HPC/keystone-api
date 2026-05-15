"""Unit tests for the `AllocationRequest` class."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.allocations.factories import AllocationRequestFactory
from apps.users.factories import TeamFactory


class CleanMethod(TestCase):
    """Test the validation of record data via the `clean` method."""

    def setUp(self) -> None:
        """Create mock user records."""

        self.team = TeamFactory()

    def test_valid_dates(self) -> None:
        """Verify the clean method returns successfully when dates are valid."""

        allocation_request = AllocationRequestFactory(
            active='2024-01-01',
            expire='2024-12-31'
        )

        allocation_request.clean()

    def test_inverted_active_after_expire(self) -> None:
        """Verify the clean method raises a `ValidationError` when active date is after expire."""

        allocation_request = AllocationRequestFactory(
            active='2024-12-31',
            expire='2024-01-01'
        )

        with self.assertRaises(ValidationError):
            allocation_request.clean()

    def test_active_equal_expire(self) -> None:
        """Verify the clean method raises a `ValidationError` when active and expire dates are equal."""

        allocation_request = AllocationRequestFactory(
            active='2024-01-01',
            expire='2024-01-01'
        )

        with self.assertRaises(ValidationError):
            allocation_request.clean()

    def test_active_is_none(self) -> None:
        """Verify the clean method does not raise when `active` is `None`."""

        allocation_request = AllocationRequestFactory(active=None, expire='2024-12-31')
        allocation_request.clean()

    def test_expire_is_none(self) -> None:
        """Verify the clean method does not raise when `expire` is `None`."""

        allocation_request = AllocationRequestFactory(active='2024-01-01', expire=None)
        allocation_request.clean()

    def test_active_and_expire_are_none(self) -> None:
        """Verify the clean method does not raise when both dates are `None`."""

        allocation_request = AllocationRequestFactory(active=None, expire=None)
        allocation_request.clean()


class GetTeamMethod(TestCase):
    """Test the retrieval of a request's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock user records."""

        self.team = TeamFactory()
        self.allocation_request = AllocationRequestFactory(team=self.team)

    def test_returns_correct_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.allocation_request.get_team())
