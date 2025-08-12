"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.research_products.models import Grant, Publication
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
    'JobStatsViewSet',
]


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve valid request status options",
        description="Retrieve valid allocation request `status` options with human-readable labels.",
        tags=["Allocations - Requests"],
        responses=inline_serializer(
            name="AllocationRequestStatusChoices",
            fields={k: serializers.CharField(default=v) for k, v in AllocationRequest.StatusChoices.choices}
        )
    )
)
class AllocationRequestStatusChoicesView(GetChoicesMixin, GenericAPIView):
    """API endpoints for exposing valid allocation request `status` values."""

    permission_classes = [IsAuthenticated]
    response_content = dict(AllocationRequest.StatusChoices.choices)


@extend_schema_view(
    list=extend_schema(
        summary="List all allocation requests",
        description="Retrieve all allocation requests visible to the current user.",
        tags=["Allocations - Requests"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an allocation request",
        description="Retrieve a single allocation request by ID.",
        tags=["Allocations - Requests"],
    ),
    create=extend_schema(
        summary="Create an allocation request",
        description="Create a new allocation request for review.",
        tags=["Allocations - Requests"],
    ),
    update=extend_schema(
        summary="Update an allocation request",
        description="Replace an existing allocation request with new values.",
        tags=["Allocations - Requests"],
    ),
    partial_update=extend_schema(
        summary="Partially update an allocation request",
        description="Apply a partial update to an existing allocation request.",
        tags=["Allocations - Requests"],
    ),
    destroy=extend_schema(
        summary="Delete an allocation request",
        description="Delete an allocation request by ID.",
        tags=["Allocations - Requests"],
    ),
)
class AllocationRequestViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing allocation requests."""

    model = AllocationRequest
    team_field = 'team'

    permission_classes = [IsAuthenticated, AllocationRequestPermissions]
    search_fields = ['title', 'description', 'team__name']
    serializer_class = AllocationRequestSerializer
    queryset = AllocationRequest.objects.prefetch_related(
        'history',
        'assignees',
        Prefetch('publications', queryset=Publication.objects.select_related('team')),
        Prefetch('grants', queryset=Grant.objects.select_related('team')),
        Prefetch('allocation_set', queryset=Allocation.objects.select_related('cluster')),
    ).select_related(
        'submitter',
        'team',
    )


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve valid review status options",
        description="Retrieve valid allocation review `status` options with human-readable labels.",
        tags=["Allocations - Reviews"],
        responses=inline_serializer(
            name="AllocationReviewStatusChoices",
            fields={k: serializers.CharField(default=v) for k, v in AllocationReview.StatusChoices.choices}
        )
    )
)
class AllocationReviewStatusChoicesView(GetChoicesMixin, GenericAPIView):
    """API endpoints for exposing valid allocation review `status` values."""

    permission_classes = [IsAuthenticated]
    response_content = dict(AllocationReview.StatusChoices.choices)


@extend_schema_view(
    list=extend_schema(
        summary="List all allocation reviews",
        description="Retrieve all allocation reviews visible to the current user.",
        tags=["Allocations - Reviews"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an allocation review",
        description="Retrieve a single allocation review by ID.",
        tags=["Allocations - Reviews"],
    ),
    create=extend_schema(
        summary="Create an allocation review",
        description="Create a new allocation review.",
        tags=["Allocations - Reviews"],
    ),
    update=extend_schema(
        summary="Update an allocation review",
        description="Replace an existing allocation review with new values.",
        tags=["Allocations - Reviews"],
    ),
    partial_update=extend_schema(
        summary="Partially update an allocation review",
        description="Apply a partial update to an existing allocation review.",
        tags=["Allocations - Reviews"],
    ),
    destroy=extend_schema(
        summary="Delete an allocation review",
        description="Delete an allocation review by ID.",
        tags=["Allocations - Reviews"],
    ),
)
class AllocationReviewViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing administrator reviews of allocation requests."""

    model = AllocationReview
    team_field = 'request__team'

    permission_classes = [IsAuthenticated, StaffWriteMemberRead]
    search_fields = ['public_comments', 'private_comments', 'request__team__name', 'request__title']
    serializer_class = AllocationReviewSerializer
    queryset = AllocationReview.objects.prefetch_related(
        'history'
    ).select_related(
        'request',
        'reviewer',
    )

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new `AllocationReview` object."""

        data = request.data.copy()
        data.setdefault('reviewer', request.user.pk)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    list=extend_schema(
        summary="List all resource allocations",
        description="Retrieve all resource allocations visible to the current user.",
        tags=["Allocations - Allocated Resources"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an resource allocation",
        description="Retrieve a single resource allocation by ID.",
        tags=["Allocations - Allocated Resources"],
    ),
    create=extend_schema(
        summary="Create an resource allocation",
        description="Create a new resource allocation.",
        tags=["Allocations - Allocated Resources"],
    ),
    update=extend_schema(
        summary="Update an resource allocation",
        description="Replace an existing resource allocation with new values.",
        tags=["Allocations - Allocated Resources"],
    ),
    partial_update=extend_schema(
        summary="Partially update an resource allocation",
        description="Apply a partial update to an existing resource allocation.",
        tags=["Allocations - Allocated Resources"],
    ),
    destroy=extend_schema(
        summary="Delete an resource allocation",
        description="Delete an resource allocation by ID.",
        tags=["Allocations - Allocated Resources"],
    ),
)
class AllocationViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing HPC resource allocations."""

    model = Allocation
    team_field = 'request__team'

    serializer_class = AllocationSerializer
    search_fields = ['request__team__name', 'request__title', 'cluster__name']
    permission_classes = [IsAuthenticated, StaffWriteMemberRead]
    queryset = Allocation.objects.prefetch_related(
        'history'
    ).select_related(
        'request',
        'cluster',
    )


@extend_schema_view(
    list=extend_schema(
        summary="List all file attachments",
        description="Retrieve metadata for all file attachments visible to the current user.",
        tags=["Allocations - Request Attachments"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a file attachment",
        description="Retrieve metadata for a single file attachment by ID.",
        tags=["Allocations - Request Attachments"],
    ),
    create=extend_schema(
        summary="Create a file attachment",
        description="Create a new file attachment.",
        tags=["Allocations - Request Attachments"],
    ),
    update=extend_schema(
        summary="Update a file attachment",
        description="Replace metadata for an existing file attachment with new values.",
        tags=["Allocations - Request Attachments"],
    ),
    partial_update=extend_schema(
        summary="Partially update a file attachment",
        description="Apply a partial update to metadata for an existing file attachment.",
        tags=["Allocations - Request Attachments"],
    ),
    destroy=extend_schema(
        summary="Delete a file attachment",
        description="Delete a file attachment and its metadata by ID.",
        tags=["Allocations - Request Attachments"],
    ),
)
class AttachmentViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing file attachments to allocation requests"""

    model = Attachment
    team_field = 'request__team'

    permission_classes = [IsAuthenticated, StaffWriteMemberRead]
    search_fields = ['path', 'request__title', 'request__submitter']
    serializer_class = AttachmentSerializer
    queryset = Attachment.objects.prefetch_related(
        'history'
    ).select_related(
        'request',
    )


@extend_schema_view(
    list=extend_schema(
        summary="List all HPC clusters",
        description="Retrieve all HPC clusters.",
        tags=["Allocations - Clusters"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an HPC cluster",
        description="Retrieve a single HPC cluster by ID.",
        tags=["Allocations - Clusters"],
    ),
    create=extend_schema(
        summary="Create an HPC cluster",
        description="Create a new HPC cluster.",
        tags=["Allocations - Clusters"],
    ),
    update=extend_schema(
        summary="Update an HPC cluster",
        description="Replace an existing HPC cluster with new values.",
        tags=["Allocations - Clusters"],
    ),
    partial_update=extend_schema(
        summary="Partially update an HPC cluster",
        description="Apply a partial update to an existing HPC cluster.",
        tags=["Allocations - Clusters"],
    ),
    destroy=extend_schema(
        summary="Delete an HPC cluster",
        description="Delete an HPC cluster by ID.",
        tags=["Allocations - Clusters"],
    ),
)
class ClusterViewSet(viewsets.ModelViewSet):
    """API endpoints for managing Slurm clusters."""

    permission_classes = [IsAuthenticated, ClusterPermissions]
    search_fields = ['name', 'description']
    serializer_class = ClusterSerializer
    queryset = Cluster.objects.all()


@extend_schema_view(
    list=extend_schema(
        summary="List all comments",
        description="Retrieve all comments visible to the current user.",
        tags=["Allocations - Request Comments"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a comment",
        description="Retrieve a single comment by ID.",
        tags=["Allocations - Request Comments"],
    ),
    create=extend_schema(
        summary="Create a comment",
        description="Create a new comment.",
        tags=["Allocations - Request Comments"],
    ),
    update=extend_schema(
        summary="Update a comment",
        description="Replace an existing comment with new values.",
        tags=["Allocations - Request Comments"],
    ),
    partial_update=extend_schema(
        summary="Partially update a comment",
        description="Apply a partial update to an existing comment.",
        tags=["Allocations - Request Comments"],
    ),
    destroy=extend_schema(
        summary="Delete a comment",
        description="Delete a comment and its metadata by ID.",
        tags=["Allocations - Request Comments"],
    ),
)
class CommentViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing comments on allocation requests."""

    model = Comment
    team_field = 'request__team'

    permission_classes = [IsAuthenticated, CommentPermissions]
    search_fields = ['content', 'request__title', 'user__username']
    serializer_class = CommentSerializer
    queryset = Comment.objects.prefetch_related(
        'history'
    ).select_related(
        'request',
        'user'
    )


@extend_schema_view(
    list=extend_schema(
        summary="List all user Slurm jobs",
        description="Retrieve status information for all Slurm jobs visible to the current user.",
        tags=["Allocations - User Jobs"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a user Slurm job",
        description="Retrieve status information for a single slurm job by ID.",
        tags=["Allocations - User Jobs"],
    )
)
class JobStatsViewSet(TeamScopedListMixin, viewsets.ReadOnlyModelViewSet):
    """API endpoints for fetching Slurm job statistics."""

    model = JobStats

    permission_classes = [IsAuthenticated, MemberReadOnly]
    search_fields = ['account', 'username', 'group', 'team__name']
    serializer_class = JobStatsSerializer
    queryset = JobStats.objects.select_related(
        'cluster',
        'team',
    )
