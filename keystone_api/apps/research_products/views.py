"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import *
from .permissions import *
from .serializers import *

__all__ = ['GrantViewSet', 'PublicationViewSet']


class PublicationViewSet(viewsets.ModelViewSet):
    """Manage metadata for research publications."""

    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    search_fields = ['title', 'abstract', 'journal', 'doi', 'team__name']
    permission_classes = [IsAuthenticated, PublicationPermissions]

    def get_queryset(self) -> list[Publication]:
        """Return a list of publications affiliated with the currently authenticated user."""

        if self.request.user.is_staff:
            return self.queryset

        return Publication.objects.affiliated_with_user(self.request.user)


class GrantViewSet(viewsets.ModelViewSet):
    """Track funding awards and grant information."""

    queryset = Grant.objects.all()
    serializer_class = GrantSerializer
    search_fields = ['title', 'agency', 'team__name']
    permission_classes = [IsAuthenticated, GrantPermissions]

    def get_queryset(self) -> list[Grant]:
        """Return a list of grants affiliated with the currently authenticated user."""

        if self.request.user.is_staff:
            return self.queryset

        return Grant.objects.affiliated_with_user(self.request.user)
