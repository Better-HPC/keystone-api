"""Unit tests for the `GetChoicesMixin` class."""

from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.views import APIView

from apps.allocations.mixins import GetChoicesMixin


class DummyChoicesView(GetChoicesMixin, APIView):
    """A dummy view for use as a testing fixture."""

    permission_classes = []
    response_content = {
        'AP': 'Approved',
        'RJ': 'Rejected',
        'PD': 'Pending'
    }


class GetMethod(TestCase):
    """Test the handling of incoming GET requests by the `get` method."""

    def test_get_returns_expected_choices(self) -> None:
        """Verify the method returns a 200 response matching the class `response_content` attribute."""

        request = RequestFactory().get('/dummy-url/')
        response = DummyChoicesView().get(request)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(DummyChoicesView.response_content, response.data)
