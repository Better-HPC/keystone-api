"""Unit tests for the `execute_step` function."""

from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import Resolver404

from apps.batch.shortcuts import execute_step


@patch('apps.batch.shortcuts.resolve')
class UrlResolution(TestCase):
    """Test the URL resolution behaviour of `execute_step`."""

    def test_strips_query_string_before_resolving_url(self, mock_resolve: Mock) -> None:
        """Verify the query string is stripped from the path before URL resolution."""

        view = Mock()
        response = Mock(status_code=200, data={})
        view.return_value = response
        mock_resolve.return_value = Mock(func=view, args=(), kwargs={})

        execute_step('GET', '/items/', {}, {'page': 2})

        resolved_path = mock_resolve.call_args[0][0]
        self.assertEqual(resolved_path, '/items/', 'Query string must be stripped before resolve()')

    def test_returns_404_for_unmatched_route(self, mock_resolve: Mock) -> None:
        """Verify an unmatched URL returns a 404 status with a detail body."""

        mock_resolve.side_effect = Resolver404()

        status_code, body = execute_step('GET', '/nonexistent/', {}, {})

        self.assertEqual(status_code, 404)
        self.assertIn('detail', body, '404 fallback should include a detail message')


@patch('apps.batch.shortcuts.resolve')
class ViewDispatch(TestCase):
    """Test that the resolved view is invoked correctly with the constructed request."""

    def test_invokes_resolved_view_with_request(self, mock_resolve: Mock) -> None:
        """Verify the resolved view is called with the constructed request."""

        view = Mock()
        response = Mock()
        response.status_code = 200
        response.data = {'id': 1}
        view.return_value = response
        mock_resolve.return_value = Mock(func=view, args=(), kwargs={})

        status_code, body = execute_step('GET', '/items/1/', {}, {})

        self.assertEqual(status_code, 200)
        self.assertEqual(body, {'id': 1})
        view.assert_called_once()

    def test_passes_url_kwargs_to_view(self, mock_resolve: Mock) -> None:
        """Verify URL-captured kwargs are forwarded as keyword arguments to the view."""

        view = Mock()
        response = Mock(status_code=200, data={})
        view.return_value = response
        mock_resolve.return_value = Mock(func=view, args=(), kwargs={'pk': '7'})

        execute_step('GET', '/items/7/', {}, {})

        _, kwargs = view.call_args
        self.assertEqual(kwargs.get('pk'), '7', 'URL-captured kwargs must reach the view')


@patch('apps.batch.shortcuts.resolve')
class ResponseHandling(TestCase):
    """Test how `execute_step` handles the response returned by the resolved view."""

    def test_renders_response_when_render_method_present(self, mock_resolve: Mock) -> None:
        """Verify response.render() is invoked on renderable responses."""

        view = Mock()
        response = Mock(status_code=200, data={'ok': True})
        view.return_value = response
        mock_resolve.return_value = Mock(func=view, args=(), kwargs={})

        execute_step('GET', '/items/', {}, {})

        response.render.assert_called_once()

    def test_returns_none_body_when_response_has_no_data(self, mock_resolve: Mock) -> None:
        """Verify a response without a `data` attribute produces a `None` body."""

        view = Mock()
        response = Mock(spec=['status_code'])
        response.status_code = 204
        view.return_value = response
        mock_resolve.return_value = Mock(func=view, args=(), kwargs={})

        status_code, body = execute_step('DELETE', '/items/1/', {}, {})

        self.assertEqual(status_code, 204)
        self.assertIsNone(body)
