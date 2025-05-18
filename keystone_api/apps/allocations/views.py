"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
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


class AllocationRequestStatusChoicesView(GenericAPIView):
    """Exposes valid values for the allocation request `status` field."""

    _resp_body = dict(AllocationRequest.StatusChoices.choices)
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={'200': _resp_body})
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return valid values for the allocation request `status` field."""

        return Response(self._resp_body, status=status.HTTP_200_OK)


class AllocationRequestViewSet(viewsets.ModelViewSet):
    """Manage allocation requests."""

    queryset = AllocationRequest.objects.all()
    serializer_class = AllocationRequestSerializer
    search_fields = ['title', 'description', 'team__name']
    permission_classes = [IsAuthenticated, AllocationRequestPermissions]

    def get_queryset(self) -> QuerySet:
        """Return a list of allocation requests for the currently authenticated user."""

        if self.request.user.is_staff:
            return self.queryset

        teams = Team.objects.teams_for_user(self.request.user)
        return AllocationRequest.objects.filter(team__in=teams)


class AllocationReviewStatusChoicesView(GenericAPIView):
    """Exposes valid values for the allocation review `status` field."""

    _resp_body = dict(AllocationReview.StatusChoices.choices)
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={'200': _resp_body})
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return valid values for the allocation review `status` field."""

        return Response(self._resp_body, status=status.HTTP_200_OK)


class AllocationReviewViewSet(viewsets.ModelViewSet):
    """Manage administrator reviews of allocation requests."""

    queryset = AllocationReview.objects.all()
    serializer_class = AllocationReviewSerializer
    search_fields = ['public_comments', 'private_comments', 'request__team__name', 'request__title']
    permission_classes = [IsAuthenticated, StaffWriteMemberRead]

    def get_queryset(self) -> QuerySet:
        """Return a list of allocation reviews for the currently authenticated user."""

        if self.request.user.is_staff:
            return self.queryset

        teams = Team.objects.teams_for_user(self.request.user)
        return AllocationReview.objects.filter(request__team__in=teams)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new `AllocationReview` object."""

        data = request.data.copy()
        data.setdefault('reviewer', request.user.pk)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AllocationViewSet(viewsets.ModelViewSet):
    """Manage HPC resource allocations."""

    queryset = Allocation.objects.all()
    serializer_class = AllocationSerializer
    search_fields = ['request__team__name', 'request__title', 'cluster__name']
    permission_classes = [IsAuthenticated, StaffWriteMemberRead]

    def get_queryset(self) -> QuerySet:
        """Return a list of allocations for the currently authenticated user."""

        if self.request.user.is_staff:
            return self.queryset

        teams = Team.objects.teams_for_user(self.request.user)
        return Allocation.objects.filter(request__team__in=teams)


class AttachmentViewSet(viewsets.ModelViewSet):
    """Files submitted as attachments to allocation requests"""

    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    search_fields = ['path', 'request__title', 'request__submitter']
    permission_classes = [IsAuthenticated, StaffWriteMemberRead]

    def get_queryset(self) -> QuerySet:
        """Return a list of attachments for the currently authenticated user."""

        if self.request.user.is_staff:
            return self.queryset

        teams = Team.objects.teams_for_user(self.request.user)
        return Attachment.objects.filter(request__team__in=teams)


class ClusterViewSet(viewsets.ModelViewSet):
    """Configuration settings for managed Slurm clusters."""

    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    search_fields = ['name', 'description']
    permission_classes = [IsAuthenticated, ClusterPermissions]


class CommentViewSet(viewsets.ModelViewSet):
    """Comments on allocation requests."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    search_fields = ['content', 'request__title', 'user__username']
    permission_classes = [IsAuthenticated, CommentPermissions]

    def get_queryset(self) -> QuerySet:
        """Return a list of comments for the currently authenticated user."""

        if self.request.user.is_staff:
            return self.queryset

        teams = Team.objects.teams_for_user(self.request.user)
        return self.queryset.filter(request__team__in=teams)
