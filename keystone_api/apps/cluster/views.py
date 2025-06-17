"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.users.mixins import UserScopedListMixin
from .models import *
from .serializers import *

__all__ = ['JobStatsViewSet']


class JobStatsViewSet(UserScopedListMixin, viewsets.ReadOnlyModelViewSet):
    """Slurm Job status and statistics."""

    model = JobStats
    queryset = JobStats.objects.all()
    serializer_class = JobStatsSerializer
    search_fields = ['title', 'agency', 'team__name']
    permission_classes = [IsAuthenticated, IsAdminUser]
