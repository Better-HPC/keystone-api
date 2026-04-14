"""Unit tests for the `HealthCheckJsonView` class."""

import json

from django.http import JsonResponse
from django.test import TestCase

from apps.health.views import HealthCheckJsonView


class RenderResponseMethod(TestCase):
    """Test the rendering of HTTP responses by the `render_response` method."""

    def test_response_is_json(self) -> None:
        """Verify the response is a JsonResponse with the correct content type."""

        response = HealthCheckJsonView().render_response([])
        self.assertIsInstance(response, JsonResponse)
        self.assertIn("application/json", response.headers.get("Content-Type", ""))

    def test_status_code_is_always_200(self) -> None:
        """Verify the status code is 200 regardless of individual health check results."""

        results = [
            {"check": "Database", "healthy": False, "error": "DB unavailable", "time_taken": 0.5},
        ]

        response = HealthCheckJsonView().render_response(results)
        self.assertEqual(response.status_code, 200)

    def test_results_wrapped_in_data_key(self) -> None:
        """Verify health check results are nested under a `data` key."""

        results = [
            {"check": "Database", "healthy": True, "error": None, "time_taken": 0.01},
            {"check": "Redis", "healthy": False, "error": "Connection refused", "time_taken": 1.0},
        ]

        response = HealthCheckJsonView().render_response(results)
        body = json.loads(response.content)

        self.assertIn("data", body)
        self.assertEqual(body["data"], results)

    def test_empty_results(self) -> None:
        """Verify an empty result list is correctly serialized."""

        response = HealthCheckJsonView().render_response([])
        body = json.loads(response.content)
        self.assertEqual(body, {"data": []})
