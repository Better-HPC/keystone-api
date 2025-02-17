"""Unit tests for the `AllocationViewSet` class."""

from django.test import TestCase

from apps.allocations.models import Allocation
from apps.allocations.tests.test_views.utils import create_viewset_request
from apps.allocations.views import AllocationViewSet
from apps.users.models import Team, User


class GetQuerysetMethod(TestCase):
    """Test the scope of database queries returned by the `get_queryset` method."""

    fixtures = ['testing_common.yaml']

    def test_get_queryset_for_staff_user(self) -> None:
        """Verify staff users are returned query including all reviews."""

        staff_user = User.objects.get(username='staff_user')

        viewset = create_viewset_request(AllocationViewSet, staff_user)
        expected_queryset = Allocation.objects.all()
        self.assertQuerySetEqual(expected_queryset, viewset.get_queryset(), ordered=False)

    def test_get_queryset_for_non_staff_user(self) -> None:
        """Verify non-staff users can only query allocations for their own teams."""

        user = User.objects.get(username='member_1')
        team = Team.objects.get(name='Team 1')

        viewset = create_viewset_request(AllocationViewSet, user)
        expected_queryset = Allocation.objects.filter(request__team__in=[team.id])
        self.assertQuerySetEqual(expected_queryset, viewset.get_queryset(), ordered=False)
