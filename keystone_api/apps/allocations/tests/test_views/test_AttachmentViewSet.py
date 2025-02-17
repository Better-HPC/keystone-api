"""Unit tests for the `AttachmentViewSet` class."""

from django.test import TestCase

from apps.allocations.models import Attachment
from apps.allocations.tests.test_views.utils import create_viewset_request
from apps.allocations.views import AttachmentViewSet
from apps.users.models import Team, User


class GetQuerysetMethod(TestCase):
    """Test the scope of database queries returned by the `get_queryset` method."""

    fixtures = ['testing_common.yaml']

    def test_get_queryset_for_staff_user(self) -> None:
        """Verify staff users are returned query including all reviews."""

        staff_user = User.objects.get(username='staff_user')

        viewset = create_viewset_request(AttachmentViewSet, staff_user)
        expected_queryset = Attachment.objects.all()
        self.assertQuerySetEqual(expected_queryset, viewset.get_queryset(), ordered=False)

    def test_get_queryset_for_non_staff_user(self) -> None:
        """Verify non-staff users can only query allocations for their own teams."""

        user = User.objects.get(username='member_1')
        team = Team.objects.get(name='Team 1')

        viewset = create_viewset_request(AttachmentViewSet, user)
        expected_queryset = Attachment.objects.filter(request__team__in=[team.id])
        self.assertQuerySetEqual(expected_queryset, viewset.get_queryset(), ordered=False)
