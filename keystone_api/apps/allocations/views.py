"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.mixins import TeamScopedListMixin
from .mixins import *
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


@extend_schema_view(  # pragma: nocover
    get=extend_schema(
        responses=inline_serializer(
            name="AllocationRequestStatusChoices",
            fields={k: serializers.CharField(default=v) for k, v in AllocationRequest.StatusChoices.choices}
        )
    )
)
class AllocationRequestStatusChoicesView(GetChoicesMixin, GenericAPIView):
    """Exposes valid values for the allocation request `status` field."""

    response_content = dict(AllocationRequest.StatusChoices.choices)
    permission_classes = [IsAuthenticated]


@extend_schema_view(  # pragma: nocover
    get=extend_schema(
        responses=inline_serializer(
            name="AllocationReviewStatusChoices",
            fields={k: serializers.CharField(default=v) for k, v in AllocationReview.StatusChoices.choices}
        )
    )
)
class AllocationReviewStatusChoicesView(GetChoicesMixin, GenericAPIView):
    """Exposes valid values for the allocation review `status` field."""

    response_content = dict(AllocationReview.StatusChoices.choices)
    permission_classes = [IsAuthenticated]


class AllocationRequestViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """Manage allocation requests."""

    model = AllocationRequest
    team_field = 'team'
    queryset = AllocationRequest.objects.all()
    serializer_class = AllocationRequestSerializer
    permission_classes = [IsAuthenticated, AllocationRequestPermissions]
    search_fields = ['title', 'description', 'team__name']


class AllocationReviewViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
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


class AllocationViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """Manage HPC resource allocations."""

    model = Allocation
    team_field = 'request__team'
    queryset = Allocation.objects.all()
    serializer_class = AllocationSerializer
    permission_classes = [IsAuthenticated, StaffWriteMemberRead]
    search_fields = ['request__team__name', 'request__title', 'cluster__name']


class AttachmentViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
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


class CommentViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """Comments on allocation requests."""

    model = Comment
    team_field = 'request__team'
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, CommentPermissions]
    search_fields = ['content', 'request__title', 'user__username']
