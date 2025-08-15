"""Reusable mixin classes for view-level logic and behavior.

Mixins provide composable building blocks for Django REST Framework views.
Each mixin defines a single, isolated piece of functionality and can be
combined with other mixins or base view classes as needed.
"""

from abc import ABC, abstractmethod

from rest_framework.request import Request
from rest_framework.response import Response

__all__ = ['GetChoicesMixin']


class GetChoicesMixin(ABC):
    """Adds a GET endpoint that returns static field choices.

    Extends Generic API views by returning a fixed value to GET requests.
    """

    @property
    @abstractmethod
    def response_content(self) -> dict:
        """The content to include in the returned GET response."""

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return a dictionary mapping choice values to human-readable names."""

        return Response(self.response_content)
