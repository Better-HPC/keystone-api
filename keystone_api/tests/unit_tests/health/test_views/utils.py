"""General utilities for setting up and supporting tests."""

from unittest.mock import MagicMock


def create_mock_plugin(status: int, pretty_status: str, critical_service: bool) -> MagicMock:
    """Create a mock health check plugin

    Args:
        status: The health check status
        pretty_status: The health check status message
        critical_service: Whether the health check represents a critical service

    Returns:
        A MagicMock object
    """

    mock_plugin = MagicMock()
    mock_plugin.status = status
    mock_plugin.pretty_status.return_value = pretty_status
    mock_plugin.critical_service = critical_service
    return mock_plugin
