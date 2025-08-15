"""Unit tests for the `GetChoicesMixin` class."""

from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase
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


class GetMethod(APITestCase):
    """Test the handling of incoming GET requests by the `get` method."""

    def test_get_returns_expected_choices(self) -> None:
        """Verify the method returns a 200 response matching the class `response_content` attribute."""

        request = Request(APIRequestFactory().get('/dummy-url/'))
        response = DummyChoicesView().get(request)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(DummyChoicesView.response_content, response.data)
