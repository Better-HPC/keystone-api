"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db.models import Model, QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.models import Team
from .models import *
from .permissions import *
from .serializers import *

__all__ = [
    'AllocationRequestStatusChoicesView',
    'AllocationRequestViewSet',
    'AllocationReviewStatusChoicesView',
    'AllocationReviewViewSet',
    'AllocationViewSet',
    'AttachmentViewSet',
    'ClusterViewSet',
    'CommentViewSet',
]


# --- Base Classes ---

class ChoicesAPIView(GenericAPIView):
    """Base class for views that return a dictionary of model field choices."""

    _choices = {}  # Must be set in subclass

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return a dictionary mapping choice values to human-readable names."""

        return Response(dict(self._choices), status=status.HTTP_200_OK)


class ScopedModelViewSet(viewsets.ModelViewSet):

    model = None  # Must be set in subclass

    def get_queryset(self) -> QuerySet:
        """Return a queryset filtered by the user's team affiliation and permissions."""

        if self.request.user.is_staff:
            return self.queryset

        teams = Team.objects.teams_for_user(self.request.user)
        return self.queryset.filter(**{f"{self.team_field}__in": teams})

    def get_object(self) -> Model:
        """Return the object and apply object-level permission checks.

        Fetches database records regardless of user affiliation and relies on
        object permissions to regulate per-record user access. This bypasses
        any filters applied to the queryset, ensuring users without appropriate
        permissions are returned a `403` error instead of a `404`.
        """

        try:
            obj = self.model.objects.get(pk=self.kwargs["pk"])

        except self.model.DoesNotExist:
            raise NotFound(f"No {self.model.__name__} matches the given query.")

        self.check_object_permissions(self.request, obj)
        return obj


# --- Concrete Views ---

@extend_schema_view(
    get=extend_schema(
        responses=inline_serializer(
            name="AllocationRequestStatusChoices",
            fields={k: serializers.CharField(default=v) for k, v in AllocationRequest.StatusChoices.choices}
        )
    )
)
class AllocationRequestStatusChoicesView(ChoicesAPIView):
    """Exposes valid values for the allocation request `status` field."""

    _choices = dict(AllocationRequest.StatusChoices.choices)
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        responses=inline_serializer(
            name="AllocationReviewStatusChoices",
            fields={k: serializers.CharField(default=v) for k, v in AllocationReview.StatusChoices.choices}
        )
    )
)
class AllocationReviewStatusChoicesView(ChoicesAPIView):
    """Exposes valid values for the allocation review `status` field."""

    _choices = dict(AllocationReview.StatusChoices.choices)
    permission_classes = [IsAuthenticated]


class AllocationRequestViewSet(ScopedModelViewSet):
    """Manage allocation requests."""

    model = AllocationRequest
    team_field = 'team'
    queryset = AllocationRequest.objects.all()
    serializer_class = AllocationRequestSerializer
    permission_classes = [IsAuthenticated, AllocationRequestPermissions]
    search_fields = ['title', 'description', 'team__name']


class AllocationReviewViewSet(ScopedModelViewSet):
    """Manage administrator reviews of allocation requests."""

    model = AllocationReview
    team_field = 'request__team'
    queryset = AllocationReview.objects.all()
    serializer_class = AllocationReviewSerializer
    permission_classes = [IsAuthenticated, StaffWriteMemberRead]
    search_fields = ['public_comments', 'private_comments', 'request__team__name', 'request__title']

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new `AllocationReview` object."""

        data = request.data.copy()
        data.setdefault('reviewer', request.user.pk)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AllocationViewSet(ScopedModelViewSet):
    """Manage HPC resource allocations."""

    model = Allocation
    team_field = 'request__team'
    queryset = Allocation.objects.all()
    serializer_class = AllocationSerializer
    permission_classes = [IsAuthenticated, StaffWriteMemberRead]
    search_fields = ['request__team__name', 'request__title', 'cluster__name']


class AttachmentViewSet(ScopedModelViewSet):
    """Files submitted as attachments to allocation requests"""

    model = Attachment
    team_field = 'request__team'
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, StaffWriteMemberRead]
    search_fields = ['path', 'request__title', 'request__submitter']


class ClusterViewSet(viewsets.ModelViewSet):
    """Configuration settings for managed Slurm clusters."""

    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    permission_classes = [IsAuthenticated, ClusterPermissions]
    search_fields = ['name', 'description']


class CommentViewSet(ScopedModelViewSet):
    """Comments on allocation requests."""

    model = Comment
    team_field = 'request__team'
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, CommentPermissions]
    search_fields = ['content', 'request__title', 'user__username']
