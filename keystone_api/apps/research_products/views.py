"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db import models
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import *
from .permissions import *
from .serializers import *

__all__ = ['GrantViewSet', 'PublicationViewSet']


class BaseAffiliatedViewSet(viewsets.ModelViewSet):
    """Base viewset for resources filtered by user affiliation."""

    model = None  # Subclasses must define this
    permission_classes = [IsAuthenticated, IsAdminUser | IsTeamMember]

    def get_queryset(self) -> models.QuerySet:
        """Return a queryset filtered by the user's team affiliation and permissions."""

        if self.request.user.is_staff:
            return self.model.objects.all()

        return self.model.objects.affiliated_with_user(self.request.user)

    def get_object(self) -> models.Model:
        """Return the object and apply object-level permission checks."""

        try:
            obj = self.model.objects.get(pk=self.kwargs["pk"])

        except self.model.DoesNotExist:
            raise NotFound(f"{self.model.__name__} not found.")

        self.check_object_permissions(self.request, obj)
        return obj


class GrantViewSet(BaseAffiliatedViewSet):
    """Track funding awards and grant information."""

    model = Grant
    queryset = Grant.objects.all()
    serializer_class = GrantSerializer
    search_fields = ['title', 'agency', 'team__name']


class PublicationViewSet(BaseAffiliatedViewSet):
    """Manage metadata for research publications."""

    model = Publication
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    search_fields = ['title', 'abstract', 'journal', 'doi', 'team__name']
