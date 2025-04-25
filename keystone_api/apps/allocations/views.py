"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import parsers, status, viewsets 
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.decorators import method_decorator 
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
import os

from apps.users.models import Team
from .models import *
from .permissions import *
from .serializers import *
from .serializers import FileUploadSerializer

__all__ = [
    'AllocationRequestStatusChoicesView',
    'AllocationRequestViewSet',
    'AllocationReviewStatusChoicesView',
    'AllocationReviewViewSet',
    'AllocationViewSet',
    'AttachmentViewSet',
    'ClusterViewSet',
    'CommentViewSet',
    'FileUploadViewSet'
]


class AllocationRequestStatusChoicesView(GenericAPIView):
    """Exposes valid values for the allocation request `status` field."""

    _resp_body = dict(AllocationRequest.StatusChoices.choices)
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={'200': _resp_body})
    def get(self, request, *args, **kwargs) -> Response:
        """Return valid values for the allocation review `status` field."""

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
    def get(self, request, *args, **kwargs) -> Response:
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

    def create(self, request, *args, **kwargs) -> Response:
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
        """Return a list of attachments for the currently authenticated user."""

        if self.request.user.is_staff:
            return self.queryset

        teams = Team.objects.teams_for_user(self.request.user)
        return self.queryset.filter(request__team__in=teams)


class FileUploadViewSet(ViewSet): 
    serializer_class = FileUploadSerializer

    def create(self, request):
        file_uploaded = request.FILES.get('file_uploaded')
        content_type = file_uploaded.content_type
        # do something with validating content type
        path = ''
        if file_uploaded:
            filename = file_uploaded.name
            path = default_storage.save(os.path.join('allocations', file_uploaded.name), file_uploaded)
            
        return Response(path)