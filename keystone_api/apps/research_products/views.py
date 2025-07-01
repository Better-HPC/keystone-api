"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.users.mixins import TeamScopedListMixin
from .models import *
from .permissions import *
from .serializers import *

__all__ = ['GrantViewSet', 'PublicationViewSet']


class GrantViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """Track funding awards and grant information."""

    model = Grant
    team_field = 'team'
    queryset = Grant.objects.all()
    serializer_class = GrantSerializer
    search_fields = ['title', 'agency', 'team__name']
    permission_classes = [IsAuthenticated, IsAdminUser | IsTeamMember]


class PublicationViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """Manage metadata for research publications."""

    model = Publication
    team_field = 'team'
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    search_fields = ['title', 'abstract', 'journal', 'doi', 'team__name']
    permission_classes = [IsAuthenticated, IsAdminUser | IsTeamMember]
