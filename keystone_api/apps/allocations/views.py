"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db.models import Prefetch, QuerySet
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
        summary="Retrieve valid request status options.",
        description="Returns valid choices for the request `status` field mapped to human-readable labels.",
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
        summary="List all allocation requests.",
        description=(
            "Returns allocation requests belonging to teams where the user is a member. "
            "Staff users can access all requests regardless of team."
        ),
        tags=["Allocations - Requests"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an allocation request.",
        description=(
            "Returns a single allocation request by its ID. "
            "General users can only access requests from teams they belong to. "
            "Staff users can access any request."
        ),
        tags=["Allocations - Requests"],
    ),
    create=extend_schema(
        summary="Create an allocation request.",
        description=(
            "Creates a new allocation request. "
            "General users can only create requests for teams where they are administrators. "
            "Staff users can create requests for any team."
        ),
        tags=["Allocations - Requests"],
    ),
    update=extend_schema(
        summary="Update an allocation request.",
        description=(
            "Replaces an existing allocation request with new values. "
            "General users can only modify requests for teams where they are administrators. "
            "Staff users can modify any request."
        ),
        tags=["Allocations - Requests"],
    ),
    partial_update=extend_schema(
        summary="Partially update an allocation request.",
        description=(
            "Partially updates an existing allocation request with new values. "
            "General users can only modify requests for teams where they are administrators. "
            "Administrators can modify any request."
        ),
        tags=["Allocations - Requests"],
    ),
    destroy=extend_schema(
        summary="Delete an allocation request.",
        description=(
            "Deletes a single allocation request by its ID. "
            "General users can only delete requests for teams where they are administrators. "
            "Staff users can delete any request."
        ),
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
        Prefetch('publications', queryset=Publication.objects.select_related('team').order_by('title')),
        Prefetch('grants', queryset=Grant.objects.select_related('team').order_by('title')),
        Prefetch('allocation_set', queryset=Allocation.objects.select_related('cluster').order_by('cluster__name')),
        Prefetch('comments', queryset=Comment.objects.select_related('user').order_by('created')),
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
        summary="List all allocation reviews.",
        description=(
            "Returns allocation reviews for requests belonging to teams where the user is a member. "
            "Staff users can access all reviews."
        ),
        tags=["Allocations - Reviews"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an allocation review.",
        description=(
            "Returns a single allocation review by its ID. "
            "General users can only access reviews for requests from teams they belong to. "
            "Staff users can access any review."
        ),
        tags=["Allocations - Reviews"],
    ),
    create=extend_schema(
        summary="Create an allocation review.",
        description=(
            "Creates a new allocation review. "
            "General users can only create reviews for requests from teams they belong to. "
            "Staff users can create reviews for any request."
        ),
        tags=["Allocations - Reviews"],
    ),
    update=extend_schema(
        summary="Update an allocation review.",
        description=(
            "Replaces an existing allocation review with new values. "
            "General users can only modify reviews for requests from teams they belong to. "
            "Staff users can modify any review."
        ),
        tags=["Allocations - Reviews"],
    ),
    partial_update=extend_schema(
        summary="Partially update an allocation review.",
        description=(
            "Partially updates an existing allocation review with new values. "
            "General users can only modify reviews for requests from teams they belong to. "
            "Staff users can modify any review."
        ),
        tags=["Allocations - Reviews"],
    ),
    destroy=extend_schema(
        summary="Delete an allocation review.",
        description=(
            "Deletes a single allocation review by its ID. "
            "General users can only delete reviews for requests from teams they belong to. "
            "Staff users can delete any review."
        ),
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
        description=(
            "Returns resource allocations granted to the current user's teams. "
            "Staff users are returned all allocations regardless of the parent team."
        ),
        tags=["Allocations - Allocated Resources"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a resource allocation.",
        description=(
            "Returns a single resource allocation by its ID. "
            "General users can only access allocations granted to teams they belong to. "
            "Staff users can access any allocation."
        ),
        tags=["Allocations - Allocated Resources"],
    ),
    create=extend_schema(
        summary="Create a resource allocation.",
        description=(
            "Creates a new resource allocation. "
            "General users can only create allocations granted to teams they belong to. "
            "Staff users can create allocations for any request."
        ),
        tags=["Allocations - Allocated Resources"],
    ),
    update=extend_schema(
        summary="Update a resource allocation.",
        description=(
            "Replaces an existing resource allocation with new values. "
            "General users can only modify allocations granted to teams they belong to. "
            "Staff users can modify any allocation."
        ),
        tags=["Allocations - Allocated Resources"],
    ),
    partial_update=extend_schema(
        summary="Partially update a resource allocation.",
        description=(
            "Partially updates an existing resource allocation with new values. "
            "General users can only modify allocations granted to teams they belong to. "
            "Staff users can modify any allocation."
        ),
        tags=["Allocations - Allocated Resources"],
    ),
    destroy=extend_schema(
        summary="Delete a resource allocation.",
        description=(
            "Deletes a resource allocation by its ID. "
            "Users can only delete allocations granted to teams they belong to. "
            "Staff can delete any allocation."
        ),
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
        description=(
            "Returns a list of file attachments on allocation requests from teams the user belongs to. "
            "Staff users are returned all attachments regardless of the parent team."
        ),
        tags=["Allocations - Request Attachments"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a file attachment",
        description=(
            "Returns a single file attachment by its ID. "
            "General users can only access attachments on requests from teams they belong to. "
            "Staff users can access any attachment."
        ),
        tags=["Allocations - Request Attachments"],
    ),
    create=extend_schema(
        summary="Create a file attachment",
        description=(
            "Creates a new file attachment on an allocation request. "
            "General users can only create attachments on requests from teams they belong to. "
            "Staff users can create attachments on any request."
        ),
        tags=["Allocations - Request Attachments"],
    ),
    update=extend_schema(
        summary="Update a file attachment",
        description=(
            "Replaces an existing file attachment with new values. "
            "General users can only modify attachments on requests from teams they belong to. "
            "Staff users can modify any attachment."
        ),
        tags=["Allocations - Request Attachments"],
    ),
    partial_update=extend_schema(
        summary="Partially update a file attachment",
        description=(
            "Partially updates an existing file attachment with new values. "
            "General users can only modify attachments on requests from teams they belong to. "
            "Staff users can modify any attachment."
        ),
        tags=["Allocations - Request Attachments"],
    ),
    destroy=extend_schema(
        summary="Delete a file attachment",
        description=(
            "Deletes a file attachment by its ID. "
            "General users only delete attachments on requests from teams they belong to. "
            "Staff users can delete any attachment."
        ),
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
        description=(
            "Create a new HPC cluster. "
            "New HPC clusters can only be created by staff users."
        ),
        tags=["Allocations - Clusters"],
    ),
    update=extend_schema(
        summary="Update an HPC cluster",
        description=(
            "Replace an existing HPC cluster with new values. "
            "HPC clusters can only be modified by staff users."
        ),
        tags=["Allocations - Clusters"],
    ),
    partial_update=extend_schema(
        summary="Partially update an HPC cluster",
        description=(
            "Apply a partial update to an existing HPC cluster. "
            "HPC clusters can only be modified by staff users."
        ),
        tags=["Allocations - Clusters"],
    ),
    destroy=extend_schema(
        summary="Delete an HPC cluster",
        description=(
            "Delete an HPC cluster by ID. "
            "HPC clusters can only be deleted by staff users."
        ),
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
        summary="List all comments.",
        description=(
            "Returns comments made on allocation requests from teams the user belongs to. "
            "Staff users are returned all comments regardless of the parent team."
        ),
        tags=["Allocations - Request Comments"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a comment.",
        description=(
            "Returns a single comment by its ID. "
            "General users can only access comments on requests from teams they belong to. "
            "Staff users can access any comment."
        ),
        tags=["Allocations - Request Comments"],
    ),
    create=extend_schema(
        summary="Create a comment.",
        description=(
            "Creates a new comment on an allocation request. "
            "General users can only create comments on requests from teams they belong to. "
            "Staff users can create comments on any request."
        ),
        tags=["Allocations - Request Comments"],
    ),
    update=extend_schema(
        summary="Update a comment.",
        description=(
            "Replaces an existing comment with new values. "
            "General users can only modify comments on requests from teams they belong to. "
            "Staff users can modify any comment."
        ),
        tags=["Allocations - Request Comments"],
    ),
    partial_update=extend_schema(
        summary="Partially update a comment",
        description=(
            "Partially updates an existing comment with new values. "
            "General users can only modify comments on requests from teams they belong to. "
            "Staff users can modify any comment."
        ),
        tags=["Allocations - Request Comments"],
    ),
    destroy=extend_schema(
        summary="Delete a comment",
        description=(
            "Deletes a comment by its ID. "
            "General users only delete comments on requests from teams they belong to. "
            "Staff users can delete any comment."
        ),
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

    def get_queryset(self) -> QuerySet:
        """Return the base queryset filtered to only list private comments for staff users."""

        queryset = super().get_queryset()

        # Only include private comments for admin users
        if self.action == 'list' and not self.request.user.is_staff:
            return queryset.filter(private=False)

        return queryset


@extend_schema_view(
    list=extend_schema(
        summary="List all user Slurm jobs.",
        description=(
            "Returns Slurm jobs belonging to teams where the user is a member. "
            "Staff users are returned all records regardless of the parent team."
        ),
        tags=["Allocations - User Jobs"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a user Slurm job.",
        description=(
            "Returns a single Slurm job by its ID. "
            "Users can only access records for teams they belong to. "
            "Staff users can access all records."
        ),
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
