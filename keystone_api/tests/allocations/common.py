"""Common tests for allocations endpoints."""

from rest_framework import status

from apps.users.factories import UserFactory


class GetResponseContentTests:
    """Test response content for an authenticated GET request matches the provided content."""

    # Defined by subclasses
    endpoint: str
    expected_content: dict

    def test_returns_expected_content(self) -> None:
        """Verify GET responses include the expected content."""

        generic_user = UserFactory(is_staff=False)
        self.client.force_authenticate(user=generic_user)

        response = self.client.get(self.endpoint)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.expected_content, response.json())
