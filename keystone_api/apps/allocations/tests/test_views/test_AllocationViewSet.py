"""Unit tests for the `AllocationViewSet` class."""

from django.test import RequestFactory, TestCase

from apps.allocations.models import Allocation, AllocationRequest, AllocationRequestReview
from apps.allocations.views import AllocationViewSet
from apps.users.models import ResearchGroup, User


class GetQueryset(TestCase):
    """Test the filtering of database records based on user permissions."""

    # TODO: Move into fixture
    def setUp(self) -> None:
        self.staff_user = User.objects.create_user('staff', 'foobar123!', is_staff=True)
        self.reviewer = User.objects.create_user('reviewer', 'foobar123!')

        self.user1 = User.objects.create_user('user1', 'foobar123!', is_staff=False)
        self.group1 = ResearchGroup.objects.create(name='group1', pi=self.user1)
        self.request1 = AllocationRequest.objects.create(title='request1', group=self.group1)
        self.review1 = AllocationRequestReview.objects.create(request=self.request1, reviewer=self.reviewer, status='AP')

        self.user2 = User.objects.create_user('user2', 'foobar123!', is_staff=False)
        self.group2 = ResearchGroup.objects.create(name='group2', pi=self.user2)
        self.request2 = AllocationRequest.objects.create(title='request2', group=self.group2)
        self.review2 = AllocationRequestReview.objects.create(request=self.request2, reviewer=self.reviewer, status='AP')

    def test_get_queryset_for_staff_user(self) -> None:
        """Test staff users can query all reviews."""

        request = RequestFactory()
        request.user = self.staff_user

        viewset = AllocationViewSet()
        viewset.request = request

        expected_queryset = Allocation.objects.all()
        self.assertQuerysetEqual(expected_queryset, viewset.get_queryset(), ordered=False)

    def test_get_queryset_for_non_staff_user(self) -> None:
        """Test non-staff users can only query allocations for their own research groups."""

        request = RequestFactory()
        request.user = self.user1

        viewset = AllocationViewSet()
        viewset.request = request

        expected_queryset = Allocation.objects.filter(request__group__in=[self.group1.id])
        self.assertQuerysetEqual(expected_queryset, viewset.get_queryset(), ordered=False)