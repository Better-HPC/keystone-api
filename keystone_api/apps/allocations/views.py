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
        tags=["Allocations - Requests"],
        summary="Retrieve valid request status options.",
        description=(
            "Returns valid choices for the request `status` field mapped to human-readable labels. "
            "Requires authentication."
        ),
        responses=inline_serializer(
            name="AllocationRequestStatusChoices",
            fields={k: serializers.CharField(default=v) for k, v in AllocationRequest.StatusChoices.choices}
        )
    )
)
class AllocationRequestStatusChoicesView(GenericAPIView):
    """API endpoints for exposing valid allocation request `status` values."""

    permission_classes = [IsAuthenticated]
    response_content = dict(AllocationRequest.StatusChoices.choices)

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return a dictionary mapping values to human-readable names."""

        return Response(self.response_content)


@extend_schema_view(
    list=extend_schema(
        tags=["Allocations - Requests"],
        summary="List allocation requests.",
        description=(
            "Returns a list of allocation requests. "
            "Requires authentication. "
            "Non-staff users are returned only requests belonging to teams where they hold membership. "
            "Staff users are returned all requests."
        ),
    ),
    retrieve=extend_schema(
        tags=["Allocations - Requests"],
        summary="Retrieve an allocation request.",
        description=(
            "Returns a single allocation request by ID. "
            "Requires authentication. "
            "Read access is granted to staff users and team members."
        ),
    ),
    create=extend_schema(
        tags=["Allocations - Requests"],
        summary="Create an allocation request.",
        description=(
            "Creates a new allocation request. "
            "Requires authentication. "
            "Write access is granted to staff users and team owners/admins."
        ),
    ),
    update=extend_schema(
        tags=["Allocations - Requests"],
        summary="Update an allocation request.",
        description=(
            "Replaces an existing allocation request with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    partial_update=extend_schema(
        tags=["Allocations - Requests"],
        summary="Partially update an allocation request.",
        description=(
            "Partially updates an existing allocation request with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    destroy=extend_schema(
        tags=["Allocations - Requests"],
        summary="Delete an allocation request.",
        description=(
            "Deletes a single allocation request by ID. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
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
        tags=["Allocations - Reviews"],
        summary="Retrieve valid review status options.",
        description=(
            "Returns valid choices for the review `status` field mapped to human-readable labels. "
            "Requires authentication."
        ),
        responses=inline_serializer(
            name="AllocationReviewStatusChoices",
            fields={k: serializers.CharField(default=v) for k, v in AllocationReview.StatusChoices.choices}
        )
    )
)
class AllocationReviewStatusChoicesView(GenericAPIView):
    """API endpoints for exposing valid allocation review `status` values."""

    permission_classes = [IsAuthenticated]
    response_content = dict(AllocationReview.StatusChoices.choices)

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return a dictionary mapping values to human-readable names."""

        return Response(self.response_content)


@extend_schema_view(
    list=extend_schema(
        tags=["Allocations - Reviews"],
        summary="List allocation reviews.",
        description=(
            "Returns a list of allocation reviews. "
            "Requires authentication. "
            "Non-staff users are returned only reviews belonging to teams where they hold membership. "
            "Staff users are returned all reviews."
        ),
    ),
    retrieve=extend_schema(
        tags=["Allocations - Reviews"],
        summary="Retrieve an allocation review.",
        description=(
            "Returns a single allocation review by ID. "
            "Requires authentication. "
            "Read access is granted to staff users and team members."
        ),
    ),
    create=extend_schema(
        tags=["Allocations - Reviews"],
        summary="Create an allocation review.",
        description=(
            "Creates a new allocation review. "
            "Requires authentication. "
            "Write access is restricted to staff users. "
            "The `reviewer` field defaults to the authenticated user if not specified."
        ),
    ),
    update=extend_schema(
        tags=["Allocations - Reviews"],
        summary="Update an allocation review.",
        description=(
            "Replaces an existing allocation review with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    partial_update=extend_schema(
        tags=["Allocations - Reviews"],
        summary="Partially update an allocation review.",
        description=(
            "Partially updates an existing allocation review with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    destroy=extend_schema(
        tags=["Allocations - Reviews"],
        summary="Delete an allocation review.",
        description=(
            "Deletes a single allocation review by ID. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
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
        tags=["Allocations - Allocated Resources"],
        summary="List resource allocations.",
        description=(
            "Returns a list of resource allocations. "
            "Requires authentication. "
            "Non-staff users are returned only allocations belonging to teams where they hold membership. "
            "Staff users are returned all allocations."
        ),
    ),
    retrieve=extend_schema(
        tags=["Allocations - Allocated Resources"],
        summary="Retrieve a resource allocation.",
        description=(
            "Returns a single resource allocation by ID. "
            "Requires authentication. "
            "Read access is granted to staff users and team members."
        ),
    ),
    create=extend_schema(
        tags=["Allocations - Allocated Resources"],
        summary="Create a resource allocation.",
        description=(
            "Creates a new resource allocation. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    update=extend_schema(
        tags=["Allocations - Allocated Resources"],
        summary="Update a resource allocation.",
        description=(
            "Replaces an existing resource allocation with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    partial_update=extend_schema(
        tags=["Allocations - Allocated Resources"],
        summary="Partially update a resource allocation.",
        description=(
            "Partially updates an existing resource allocation with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    destroy=extend_schema(
        tags=["Allocations - Allocated Resources"],
        summary="Delete a resource allocation.",
        description=(
            "Deletes a resource allocation by ID. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
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
        tags=["Allocations - Request Attachments"],
        summary="List file attachments.",
        description=(
            "Returns a list of file attachments. "
            "Requires authentication. "
            "Non-staff users are returned only attachments belonging to teams where they hold membership. "
            "Staff users are returned all attachments."
        ),
    ),
    retrieve=extend_schema(
        tags=["Allocations - Request Attachments"],
        summary="Retrieve a file attachment.",
        description=(
            "Returns a single file attachment by ID. "
            "Requires authentication. "
            "Read access is granted to staff users and team members."
        ),
    ),
    create=extend_schema(
        tags=["Allocations - Request Attachments"],
        summary="Create a file attachment.",
        description=(
            "Creates a new file attachment on an allocation request. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    update=extend_schema(
        tags=["Allocations - Request Attachments"],
        summary="Update a file attachment.",
        description=(
            "Replaces an existing file attachment with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    partial_update=extend_schema(
        tags=["Allocations - Request Attachments"],
        summary="Partially update a file attachment.",
        description=(
            "Partially updates an existing file attachment with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    destroy=extend_schema(
        tags=["Allocations - Request Attachments"],
        summary="Delete a file attachment.",
        description=(
            "Deletes a file attachment by ID. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
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
        tags=["Allocations - Clusters"],
        summary="List HPC clusters.",
        description=(
            "Returns a list of HPC clusters. "
            "Requires authentication. "
            "Non-staff users are returned only clusters accessible based on each cluster's access mode "
            "(open, whitelist, or blacklist) and the user's team memberships. "
            "Staff users are returned all clusters."
        ),
    ),
    retrieve=extend_schema(
        tags=["Allocations - Clusters"],
        summary="Retrieve an HPC cluster.",
        description=(
            "Returns a single HPC cluster by ID. "
            "Requires authentication."
        ),
    ),
    create=extend_schema(
        tags=["Allocations - Clusters"],
        summary="Create an HPC cluster.",
        description=(
            "Creates a new HPC cluster. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    update=extend_schema(
        tags=["Allocations - Clusters"],
        summary="Update an HPC cluster.",
        description=(
            "Replaces an existing HPC cluster with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    partial_update=extend_schema(
        tags=["Allocations - Clusters"],
        summary="Partially update an HPC cluster.",
        description=(
            "Partially updates an existing HPC cluster with new values. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
    destroy=extend_schema(
        tags=["Allocations - Clusters"],
        summary="Delete an HPC cluster.",
        description=(
            "Deletes an HPC cluster by ID. "
            "Requires authentication. "
            "Write access is restricted to staff users."
        ),
    ),
)
class ClusterViewSet(viewsets.ModelViewSet):
    """API endpoints for managing Slurm clusters."""

    permission_classes = [IsAuthenticated, ClusterPermissions]
    search_fields = ['name', 'description']
    serializer_class = ClusterSerializer
    queryset = Cluster.objects.all()

    def get_queryset(self) -> QuerySet[Cluster]:
        """Return a queryset of clusters visible to the requesting user.

        For the 'list' action, clusters are filters by the cluster's access
        mode and the requesting user's team memberships.

        - OPEN clusters are always included.
        - WHITELIST User must belong to an allowed team.
        - BLACKLIST User must NOT belong to an allowed team.

        Staff users are exempt from record filtering.
        Other actions (retrieve, update, delete) are also exempt from record filtering.

        Returns:
            A queryset for filtered `Cluster` records.
        """

        qs = super().get_queryset()

        # Only filter for list operations
        if self.action == 'list' and not self.request.user.is_staff:
            user_teams = self.request.user.get_all_teams().values_list('id', flat=True)

            # Clusters open to all
            open_clusters = qs.filter(access_mode=Cluster.AccessChoices.OPEN)

            # Clusters whitelisting specific teams
            whitelisted_clusters = qs.filter(
                access_mode=Cluster.AccessChoices.WHITELIST,
                access_teams__in=user_teams
            )

            # Clusters blacklisting specific teams
            blacklisted_clusters = qs.filter(
                access_mode=Cluster.AccessChoices.BLACKLIST
            ).exclude(access_teams__in=user_teams)

            # Combine querysets
            qs = (open_clusters | whitelisted_clusters | blacklisted_clusters).distinct()

        return qs


@extend_schema_view(
    list=extend_schema(
        tags=["Allocations - Request Comments"],
        summary="List comments.",
        description=(
            "Returns a list of comments made on allocation requests. "
            "Requires authentication. "
            "Non-staff users are returned only public comments belonging to teams where they hold membership. "
            "Staff users are returned all comments, including private comments."
        ),
    ),
    retrieve=extend_schema(
        tags=["Allocations - Request Comments"],
        summary="Retrieve a comment.",
        description=(
            "Returns a single comment by ID. "
            "Requires authentication. "
            "Read access is granted to staff users and team members for public comments. "
            "Private comments are only accessible to staff users."
        ),
    ),
    create=extend_schema(
        tags=["Allocations - Request Comments"],
        summary="Create a comment.",
        description=(
            "Creates a new comment on an allocation request. "
            "Requires authentication. "
            "Write access is granted to staff users and team members. "
            "Only staff users may create comments marked as private."
        ),
    ),
    update=extend_schema(
        tags=["Allocations - Request Comments"],
        summary="Update a comment.",
        description=(
            "Replaces an existing comment with new values. "
            "Requires authentication. "
            "Write access is granted to staff users and team members for public comments. "
            "Only staff users may modify private comments."
        ),
    ),
    partial_update=extend_schema(
        tags=["Allocations - Request Comments"],
        summary="Partially update a comment.",
        description=(
            "Partially updates an existing comment with new values. "
            "Requires authentication. "
            "Write access is granted to staff users and team members for public comments. "
            "Only staff users may modify private comments."
        ),
    ),
    destroy=extend_schema(
        tags=["Allocations - Request Comments"],
        summary="Delete a comment.",
        description=(
            "Deletes a comment by ID. "
            "Requires authentication. "
            "Write access is granted to staff users and team members for public comments. "
            "Only staff users may delete private comments."
        ),
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
        tags=["Allocations - User Jobs"],
        summary="List user Slurm jobs.",
        description=(
            "Returns a list of Slurm jobs. "
            "Requires authentication. "
            "Non-staff users are returned only jobs belonging to teams where they hold membership. "
            "Staff users are returned all jobs."
        ),
    ),
    retrieve=extend_schema(
        tags=["Allocations - User Jobs"],
        summary="Retrieve a user Slurm job.",
        description=(
            "Returns a single Slurm job by Keystone ID. "
            "Requires authentication. "
            "Read access is granted to staff users and team members."
        ),
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
